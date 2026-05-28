"""Validation helpers for token usage payloads."""

from __future__ import annotations

from typing import Any

from src.tracking.token_contracts import TOKEN_SOURCE_VALUES
from src.tracking.token_result import build_failure_usage_result
from src.reporting.report_metrics import safe_int, safe_text


class TokenValidator:
    """Validate token usage structures and aggregations."""

    def validate(self, usage_payload: dict[str, Any]) -> dict[str, Any]:
        """Validate a normalized token usage payload."""

        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}

        if not isinstance(usage_payload, dict):
            return {"valid": False, "warnings": [], "errors": ["Usage payload must be a dictionary."], "checks": {}}

        provider = safe_text(usage_payload.get("provider"), limit=80)
        model = safe_text(usage_payload.get("model"), limit=80)
        input_tokens = safe_int(usage_payload.get("input_tokens"), -1)
        output_tokens = safe_int(usage_payload.get("output_tokens"), -1)
        total_tokens = safe_int(usage_payload.get("total_tokens"), -1)
        estimated = usage_payload.get("estimated")
        source = safe_text(usage_payload.get("source"), limit=80)

        checks["provider_present"] = bool(provider)
        checks["model_present"] = bool(model)
        checks["estimated_present"] = isinstance(estimated, bool)
        checks["source_valid"] = source in TOKEN_SOURCE_VALUES
        checks["non_negative_counts"] = all(value >= 0 for value in (input_tokens, output_tokens, total_tokens))
        checks["total_matches_sum"] = total_tokens == (input_tokens + output_tokens) if input_tokens >= 0 and output_tokens >= 0 and total_tokens >= 0 else False

        if not provider:
            errors.append("Provider is required.")
        if input_tokens < 0 or output_tokens < 0 or total_tokens < 0:
            errors.append("Token counts must be non-negative integers.")
        if not checks["estimated_present"]:
            warnings.append("Estimated flag is missing or malformed.")
        if not checks["source_valid"]:
            warnings.append("Token source is not recognized.")
        if provider and not model:
            warnings.append("Model is missing for a token usage payload.")
        if checks["total_matches_sum"] is False and input_tokens >= 0 and output_tokens >= 0 and total_tokens >= 0:
            warnings.append("Total tokens do not match input plus output tokens.")

        return {"valid": not errors, "warnings": warnings, "errors": errors, "checks": checks}

    def validate_aggregation(self, summary: dict[str, Any]) -> dict[str, Any]:
        """Validate aggregated usage totals."""

        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}

        if not isinstance(summary, dict):
            return {"valid": False, "warnings": [], "errors": ["Aggregation summary must be a dictionary."], "checks": {}}

        for key in ("total_input_tokens", "total_output_tokens", "total_tokens", "records_count", "estimated_records", "real_usage_records"):
            checks[f"{key}_valid"] = safe_int(summary.get(key), -1) >= 0
            if not checks[f"{key}_valid"]:
                errors.append(f"Invalid aggregation value for {key}.")

        input_tokens = safe_int(summary.get("total_input_tokens"), -1)
        output_tokens = safe_int(summary.get("total_output_tokens"), -1)
        total_tokens = safe_int(summary.get("total_tokens"), -1)
        if total_tokens >= 0 and input_tokens >= 0 and output_tokens >= 0 and total_tokens != input_tokens + output_tokens:
            warnings.append("Aggregated total tokens do not match input plus output tokens.")

        return {"valid": not errors, "warnings": warnings, "errors": errors, "checks": checks}
