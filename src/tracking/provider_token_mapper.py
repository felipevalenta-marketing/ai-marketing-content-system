"""Provider token normalization helpers."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_int, safe_text
from src.tracking.token_contracts import TOKEN_FIELD_ALIASES
from src.tracking.token_result import build_unavailable_usage_result


class ProviderTokenMapper:
    """Normalize provider-specific token usage structures."""

    def normalize(
        self,
        provider: str,
        usage_payload: dict[str, Any] | Any,
        *,
        model: str = "",
        metadata: dict[str, Any] | None = None,
        execution_id: str = "",
        module: str = "",
        operation: str = "",
        campaign_id: str = "",
        asset_type: str = "",
    ) -> dict[str, Any]:
        """Normalize a provider usage payload into the internal schema."""

        provider_name = safe_text(provider, limit=80).lower()
        normalized = self._coerce_mapping(usage_payload)
        if not normalized:
            return build_unavailable_usage_result(
                provider=provider_name,
                model=model,
                execution_id=execution_id,
                module=module,
                operation=operation,
                campaign_id=campaign_id,
                asset_type=asset_type,
                metadata=metadata or {},
                warnings=["Provider token usage unavailable."],
            )

        input_tokens = self._extract_int(normalized, "input_tokens", "prompt_tokens")
        output_tokens = self._extract_int(normalized, "output_tokens", "completion_tokens")
        total_tokens = self._extract_int(normalized, "total_tokens")
        if total_tokens < 0 and input_tokens >= 0 and output_tokens >= 0:
            total_tokens = input_tokens + output_tokens
        if input_tokens < 0 and output_tokens < 0 and total_tokens < 0:
            return build_unavailable_usage_result(
                provider=provider_name,
                model=model,
                execution_id=execution_id,
                module=module,
                operation=operation,
                campaign_id=campaign_id,
                asset_type=asset_type,
                metadata=metadata or {},
                warnings=["Provider token usage payload did not include usable token fields."],
            )

        input_tokens = max(0, input_tokens)
        output_tokens = max(0, output_tokens)
        total_tokens = max(0, total_tokens)
        if total_tokens == 0:
            total_tokens = input_tokens + output_tokens

        return {
            "success": True,
            "provider": provider_name,
            "model": safe_text(model or normalized.get("model", ""), limit=80),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated": False,
            "source": "provider_usage",
            "execution_id": execution_id,
            "module": module,
            "operation": operation,
            "campaign_id": campaign_id,
            "asset_type": asset_type,
            "metadata": metadata or {},
            "warnings": [],
            "errors": [],
        }

    def _coerce_mapping(self, usage_payload: dict[str, Any] | Any) -> dict[str, Any]:
        """Convert provider usage payloads into dictionaries when possible."""

        if isinstance(usage_payload, dict):
            return dict(usage_payload)
        if usage_payload is None:
            return {}
        if hasattr(usage_payload, "model_dump"):
            try:
                dumped = usage_payload.model_dump()
                if isinstance(dumped, dict):
                    return dict(dumped)
            except Exception:
                return {}
        if hasattr(usage_payload, "to_dict"):
            try:
                dumped = usage_payload.to_dict()
                if isinstance(dumped, dict):
                    return dict(dumped)
            except Exception:
                return {}
        data: dict[str, Any] = {}
        for field_name in ("input_tokens", "output_tokens", "total_tokens", "prompt_tokens", "completion_tokens", "model"):
            if hasattr(usage_payload, field_name):
                data[field_name] = getattr(usage_payload, field_name)
        return data

    def _extract_int(self, payload: dict[str, Any], *keys: str) -> int:
        for key in keys:
            value = payload.get(key)
            if value is None:
                continue
            number = safe_int(value, -1)
            if number >= 0:
                return number
        return -1
