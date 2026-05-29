"""Token tracking orchestration."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_dict, safe_text, utc_now_iso
from src.tracking.provider_token_mapper import ProviderTokenMapper
from src.tracking.token_aggregator import TokenAggregator
from src.tracking.token_estimator import TokenEstimator
from src.tracking.token_result import (
    build_estimated_usage_result,
    build_failure_usage_result,
    build_success_usage_result,
    build_unavailable_usage_result,
)
from src.tracking.token_validator import TokenValidator
from src.observability.metrics_registry import get_metrics_registry
from src.utils.logger import get_logger, log_warning


class TokenTracker:
    """Central orchestration for token usage normalization and aggregation."""

    def __init__(
        self,
        mapper: ProviderTokenMapper | None = None,
        estimator: TokenEstimator | None = None,
        aggregator: TokenAggregator | None = None,
        validator: TokenValidator | None = None,
        logger: Any | None = None,
    ) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.mapper = mapper or ProviderTokenMapper()
        self.estimator = estimator or TokenEstimator()
        self.aggregator = aggregator or TokenAggregator()
        self.validator = validator or TokenValidator()

    def track_usage(self, usage_payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Normalize a provider usage payload or estimate when necessary."""

        payload = safe_dict(usage_payload)
        meta = safe_dict(metadata)
        provider = safe_text(payload.get("provider") or meta.get("provider"), limit=80)
        model = safe_text(payload.get("model") or meta.get("model"), limit=80)
        execution_id = safe_text(meta.get("execution_id") or meta.get("execution", {}).get("started_at"), limit=120)
        module = safe_text(meta.get("module") or meta.get("pipeline_stage") or "", limit=120)
        operation = safe_text(meta.get("operation") or meta.get("route") or "", limit=120)
        campaign_id = safe_text(meta.get("campaign_id") or "", limit=120)
        asset_type = safe_text(meta.get("asset_type") or meta.get("content_type") or "", limit=120)

        if payload:
            normalized = self.mapper.normalize(
                provider=provider,
                usage_payload=payload,
                model=model,
                metadata=meta,
                execution_id=execution_id,
                module=module,
                operation=operation,
                campaign_id=campaign_id,
                asset_type=asset_type,
            )
        else:
            normalized = build_unavailable_usage_result(
                provider=provider,
                model=model,
                execution_id=execution_id,
                module=module,
                operation=operation,
                campaign_id=campaign_id,
                asset_type=asset_type,
                metadata=meta,
                warnings=["Token usage payload is missing."],
            )

        validation = self.validator.validate(normalized)
        if validation["warnings"]:
            normalized["warnings"] = list(dict.fromkeys(list(normalized.get("warnings", [])) + validation["warnings"]))
        if validation["errors"]:
            normalized["errors"] = list(dict.fromkeys(list(normalized.get("errors", [])) + validation["errors"]))
        normalized["validation"] = validation
        normalized["metadata"] = {**meta, **safe_dict(normalized.get("metadata"))}
        metrics = get_metrics_registry()
        labels = {
            "workflow_id": safe_text(meta.get("workflow_id") or meta.get("execution_id") or "", limit=120),
            "organization_id": safe_text(meta.get("organization_id") or "", limit=120),
            "brand_id": safe_text(meta.get("brand_id") or meta.get("brand") or "", limit=120),
        }
        metrics.increment_counter("token_usage_total", labels=labels, value=float(normalized.get("total_tokens", 0) or 0))
        return normalized

    def record_generation(self, usage_payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record a generation usage payload."""

        return self.track_usage(usage_payload, metadata=metadata)

    def record_estimated_usage(
        self,
        input_text: str,
        output_text: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record an estimated usage record from text."""

        meta = safe_dict(metadata)
        return self.estimator.estimate_usage(
            input_text=input_text,
            output_text=output_text,
            provider=safe_text(meta.get("provider"), limit=80),
            model=safe_text(meta.get("model"), limit=80),
            metadata=meta,
            execution_id=safe_text(meta.get("execution_id") or meta.get("execution", {}).get("started_at"), limit=120),
            module=safe_text(meta.get("module") or meta.get("pipeline_stage") or "", limit=120),
            operation=safe_text(meta.get("operation") or meta.get("route") or "", limit=120),
            campaign_id=safe_text(meta.get("campaign_id") or "", limit=120),
            asset_type=safe_text(meta.get("asset_type") or meta.get("content_type") or "", limit=120),
        )

    def aggregate_execution(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate usage across a single execution."""

        return self.aggregator.aggregate_by_execution(records)

    def aggregate_campaign(self, records: list[dict[str, Any]], campaign_id: str) -> dict[str, Any]:
        """Aggregate usage for a campaign id."""

        summary = self.aggregator.aggregate_by_campaign(records)
        summary["campaign_id"] = safe_text(campaign_id, limit=120)
        return summary

    def aggregate_asset(self, records: list[dict[str, Any]], asset_type: str) -> dict[str, Any]:
        """Aggregate usage for an asset type."""

        summary = self.aggregator.aggregate_by_asset(records)
        summary["asset_type"] = safe_text(asset_type, limit=120)
        return summary

    def get_total_usage(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a total usage summary."""

        return self.aggregator.summarize_usage(records)

    def build_result(
        self,
        *,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        estimated: bool,
        source: str,
        execution_id: str = "",
        module: str = "",
        operation: str = "",
        campaign_id: str = "",
        asset_type: str = "",
        metadata: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build a token usage result."""

        return build_success_usage_result(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated=estimated,
            source=source,
            execution_id=execution_id,
            module=module,
            operation=operation,
            campaign_id=campaign_id,
            asset_type=asset_type,
            metadata=metadata,
            warnings=warnings,
            errors=errors,
        )

    def build_estimated_result(self, input_text: str, output_text: str | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build an estimated usage result."""

        return self.record_estimated_usage(input_text=input_text, output_text=output_text, metadata=metadata)

    def build_unavailable_result(self, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build an unavailable usage result."""

        meta = safe_dict(metadata)
        return build_unavailable_usage_result(
            provider=safe_text(meta.get("provider"), limit=80),
            model=safe_text(meta.get("model"), limit=80),
            execution_id=safe_text(meta.get("execution_id") or meta.get("execution", {}).get("started_at"), limit=120),
            module=safe_text(meta.get("module") or meta.get("pipeline_stage") or "", limit=120),
            operation=safe_text(meta.get("operation") or meta.get("route") or "", limit=120),
            campaign_id=safe_text(meta.get("campaign_id") or "", limit=120),
            asset_type=safe_text(meta.get("asset_type") or meta.get("content_type") or "", limit=120),
            metadata=meta,
        )

    def warn_if_suspicious(self, usage: dict[str, Any]) -> list[str]:
        """Return non-blocking warnings for unusual token usage."""

        warnings: list[str] = []
        total_tokens = int(usage.get("total_tokens", 0) or 0)
        if total_tokens >= 12000:
            warnings.append("Suspiciously high token usage detected.")
        return warnings
