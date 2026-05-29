"""Cost tracking orchestration."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_dict, safe_text
from src.reporting.report_metrics import safe_int
from src.tracking.cost_aggregator import CostAggregator
from src.tracking.cost_calculator import CostCalculator
from src.tracking.cost_result import (
    build_failure_cost_result,
    build_success_cost_result,
    build_unknown_pricing_result,
)
from src.tracking.cost_validator import CostValidator
from src.tracking.provider_pricing_mapper import ProviderPricingMapper
from src.observability.metrics_registry import get_metrics_registry
from src.utils.logger import get_logger, log_warning
import json


class CostTracker:
    """Central orchestration for cost estimation and aggregation."""

    def __init__(
        self,
        mapper: ProviderPricingMapper | None = None,
        calculator: CostCalculator | None = None,
        aggregator: CostAggregator | None = None,
        validator: CostValidator | None = None,
        logger: Any | None = None,
        *,
        enable_fallback: bool = True,
        default_currency: str = "USD",
        round_decimals: int = 6,
    ) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.mapper = mapper or ProviderPricingMapper()
        self.calculator = calculator or CostCalculator()
        self.aggregator = aggregator or CostAggregator()
        self.validator = validator or CostValidator()
        self.enable_fallback = enable_fallback
        self.default_currency = default_currency
        self.round_decimals = round_decimals

    def track_cost(self, token_usage: dict[str, Any] | None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Normalize token usage into a cost record."""

        meta = safe_dict(metadata)
        usage = safe_dict(token_usage)
        fallback_usage = safe_dict(meta.get("fallback_token_usage"))
        if not usage and self.enable_fallback and fallback_usage:
            usage = fallback_usage
            meta = {**meta, "fallback_used": True}

        if not usage:
            result = build_unknown_pricing_result(
                provider=safe_text(meta.get("provider"), limit=80),
                model=safe_text(meta.get("model"), limit=80),
                currency=safe_text(meta.get("currency"), limit=32) or self.default_currency,
                execution_id=safe_text(meta.get("execution_id"), limit=120),
                module=safe_text(meta.get("module"), limit=120),
                operation=safe_text(meta.get("operation"), limit=120),
                campaign_id=safe_text(meta.get("campaign_id"), limit=120),
                asset_type=safe_text(meta.get("asset_type"), limit=120),
                metadata=meta,
                warnings=["Token usage unavailable. Cost tracking is partial."],
            )
            result["estimated_cost"] = True
            result["pricing_found"] = False
            return result

        normalized = self._normalize_usage(usage, meta)
        pricing = self.mapper.lookup_pricing(normalized["provider"], normalized["model"])
        pricing_found = bool(pricing.get("pricing_found", False))

        if not pricing_found:
            result = build_unknown_pricing_result(
                provider=normalized["provider"],
                model=normalized["model"],
                currency=pricing.get("currency") or self.default_currency,
                input_tokens=normalized["input_tokens"],
                output_tokens=normalized["output_tokens"],
                cached_input_tokens=normalized["cached_input_tokens"],
                total_tokens=normalized["total_tokens"],
                execution_id=normalized["execution_id"],
                module=normalized["module"],
                operation=normalized["operation"],
                campaign_id=normalized["campaign_id"],
                asset_type=normalized["asset_type"],
                metadata={**meta, "pricing": pricing},
                warnings=[pricing.get("notes") or "Pricing not found for provider/model."],
            )
            result["estimated_tokens"] = bool(normalized["estimated_tokens"])
            validation = self.validator.validate(result)
            result["warnings"] = list(dict.fromkeys(list(result.get("warnings", [])) + validation.get("warnings", [])))
            result["errors"] = list(dict.fromkeys(list(result.get("errors", [])) + validation.get("errors", [])))
            return result

        costs = self.calculator.calculate_cost_record(normalized, pricing, round_decimals=self.round_decimals)
        result = build_success_cost_result(
            provider=normalized["provider"],
            model=normalized["model"],
            currency=costs.get("currency", pricing.get("currency", self.default_currency)),
            input_tokens=normalized["input_tokens"],
            output_tokens=normalized["output_tokens"],
            cached_input_tokens=normalized["cached_input_tokens"],
            total_tokens=normalized["total_tokens"],
            input_cost=costs["input_cost"],
            output_cost=costs["output_cost"],
            cached_input_cost=costs["cached_input_cost"],
            total_cost=costs["total_cost"],
            estimated_tokens=bool(normalized["estimated_tokens"]),
            estimated_cost=bool(normalized["estimated_tokens"]),
            pricing_found=True,
            pricing_version=safe_text(pricing.get("pricing_version"), limit=80),
            pricing_source=safe_text(pricing.get("pricing_source"), limit=80),
            execution_id=normalized["execution_id"],
            module=normalized["module"],
            operation=normalized["operation"],
            campaign_id=normalized["campaign_id"],
            asset_type=normalized["asset_type"],
            metadata={**meta, "pricing": pricing},
            warnings=list(normalized["warnings"]),
            errors=list(normalized["errors"]),
        )
        validation = self.validator.validate(result)
        result["warnings"] = list(dict.fromkeys(list(result.get("warnings", [])) + validation.get("warnings", [])))
        result["errors"] = list(dict.fromkeys(list(result.get("errors", [])) + validation.get("errors", [])))
        get_metrics_registry().increment_counter(
            "cost_total",
            labels={
                "workflow_id": safe_text(meta.get("workflow_id") or meta.get("execution_id") or "", limit=120),
                "organization_id": safe_text(meta.get("organization_id") or "", limit=120),
                "brand_id": safe_text(meta.get("brand_id") or meta.get("brand") or "", limit=120),
            },
            value=float(result.get("total_cost", 0.0) or 0.0),
        )
        return result

    def record_generation_cost(self, token_usage: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """Record a generation cost payload."""

        return self.track_cost(token_usage, metadata=metadata)

    def aggregate_execution_cost(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate cost across a single execution."""

        return self.aggregator.aggregate_by_execution(records)

    def aggregate_campaign_cost(self, records: list[dict[str, Any]], campaign_id: str) -> dict[str, Any]:
        """Aggregate cost for a campaign id."""

        summary = self.aggregator.aggregate_by_campaign(records)
        summary["campaign_id"] = safe_text(campaign_id, limit=120)
        return summary

    def aggregate_asset_cost(self, records: list[dict[str, Any]], asset_type: str) -> dict[str, Any]:
        """Aggregate cost for an asset type."""

        summary = self.aggregator.aggregate_by_asset(records)
        summary["asset_type"] = safe_text(asset_type, limit=120)
        return summary

    def get_total_cost(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a total cost summary."""

        return self.aggregator.summarize_cost(records)

    def build_result(
        self,
        *,
        provider: str,
        model: str,
        currency: str,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int,
        total_tokens: int,
        input_cost: float,
        output_cost: float,
        cached_input_cost: float,
        total_cost: float,
        estimated_tokens: bool,
        estimated_cost: bool,
        pricing_found: bool,
        pricing_version: str,
        pricing_source: str,
        execution_id: str = "",
        module: str = "",
        operation: str = "",
        campaign_id: str = "",
        asset_type: str = "",
        metadata: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build a cost result."""

        return build_success_cost_result(
            provider=provider,
            model=model,
            currency=currency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            cached_input_cost=cached_input_cost,
            total_cost=total_cost,
            estimated_tokens=estimated_tokens,
            estimated_cost=estimated_cost,
            pricing_found=pricing_found,
            pricing_version=pricing_version,
            pricing_source=pricing_source,
            execution_id=execution_id,
            module=module,
            operation=operation,
            campaign_id=campaign_id,
            asset_type=asset_type,
            metadata=metadata,
            warnings=warnings,
            errors=errors,
        )

    def _normalize_usage(self, usage: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
        """Normalize a token usage payload into a cost-friendly structure."""

        provider = safe_text(usage.get("provider") or metadata.get("provider"), limit=80).lower()
        model = safe_text(usage.get("model") or metadata.get("model"), limit=80)
        input_tokens = max(0, safe_int(usage.get("input_tokens") if usage.get("input_tokens") is not None else usage.get("prompt_tokens"), 0))
        output_tokens = max(0, safe_int(usage.get("output_tokens") if usage.get("output_tokens") is not None else usage.get("completion_tokens"), 0))
        cached_input_tokens = max(0, safe_int(usage.get("cached_input_tokens") if usage.get("cached_input_tokens") is not None else usage.get("cached_tokens"), 0))
        total_tokens = max(0, safe_int(usage.get("total_tokens"), input_tokens + output_tokens))
        estimated_tokens = bool(usage.get("estimated", False))
        return {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_input_tokens": cached_input_tokens,
            "total_tokens": total_tokens,
            "estimated_tokens": estimated_tokens,
            "execution_id": safe_text(usage.get("execution_id") or metadata.get("execution_id"), limit=120),
            "module": safe_text(usage.get("module") or metadata.get("module") or metadata.get("pipeline_stage") or "", limit=120),
            "operation": safe_text(usage.get("operation") or metadata.get("operation") or "", limit=120),
            "campaign_id": safe_text(usage.get("campaign_id") or metadata.get("campaign_id") or "", limit=120),
            "asset_type": safe_text(usage.get("asset_type") or metadata.get("asset_type") or metadata.get("content_type") or "", limit=120),
            "warnings": list(dict.fromkeys([safe_text(item, limit=240) for item in usage.get("warnings", []) if safe_text(item, limit=240)])),
            "errors": list(dict.fromkeys([safe_text(item, limit=240) for item in usage.get("errors", []) if safe_text(item, limit=240)])),
        }

    def warn_if_suspicious(self, cost: dict[str, Any]) -> list[str]:
        """Return non-blocking warnings for unusual costs."""

        warnings: list[str] = []
        total_cost = float(cost.get("total_cost", 0.0) or 0.0)
        if total_cost >= 50.0:
            warnings.append("Suspiciously high estimated cost detected.")
        return warnings


if __name__ == "__main__":
    demo_tracker = CostTracker()
    sample_usage = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "input_tokens": 1200,
        "output_tokens": 300,
        "cached_input_tokens": 100,
        "total_tokens": 1500,
        "estimated": False,
        "source": "provider_usage",
        "execution_id": "exec-demo",
        "module": "generation",
        "operation": "demo",
        "campaign_id": "campaign-demo",
        "asset_type": "instagram_post",
        "metadata": {},
        "warnings": [],
        "errors": [],
    }
    result = demo_tracker.track_cost(sample_usage, metadata={"provider": "openai", "model": "gpt-4o-mini"})
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(json.dumps(demo_tracker.get_total_cost([result]), indent=2, ensure_ascii=False))
