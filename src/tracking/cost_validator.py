"""Validation helpers for cost tracking payloads."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_float, safe_int, safe_text


class CostValidator:
    """Validate cost usage structures and aggregations."""

    def validate(self, cost_payload: dict[str, Any]) -> dict[str, Any]:
        """Validate a normalized cost payload."""

        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}

        if not isinstance(cost_payload, dict):
            return {"valid": False, "warnings": [], "errors": ["Cost payload must be a dictionary."], "checks": {}}

        provider = safe_text(cost_payload.get("provider"), limit=80)
        model = safe_text(cost_payload.get("model"), limit=80)
        currency = safe_text(cost_payload.get("currency"), limit=32)
        input_tokens = safe_int(cost_payload.get("input_tokens"), -1)
        output_tokens = safe_int(cost_payload.get("output_tokens"), -1)
        cached_input_tokens = safe_int(cost_payload.get("cached_input_tokens"), -1)
        total_tokens = safe_int(cost_payload.get("total_tokens"), -1)
        input_cost = safe_float(cost_payload.get("input_cost"), -1.0)
        output_cost = safe_float(cost_payload.get("output_cost"), -1.0)
        cached_input_cost = safe_float(cost_payload.get("cached_input_cost"), -1.0)
        total_cost = safe_float(cost_payload.get("total_cost"), -1.0)
        estimated_tokens = cost_payload.get("estimated_tokens")
        estimated_cost = cost_payload.get("estimated_cost")
        pricing_found = cost_payload.get("pricing_found")
        pricing_version = safe_text(cost_payload.get("pricing_version"), limit=80)

        checks["provider_present"] = bool(provider)
        checks["model_present"] = bool(model)
        checks["currency_present"] = bool(currency)
        checks["estimated_tokens_present"] = isinstance(estimated_tokens, bool)
        checks["estimated_cost_present"] = isinstance(estimated_cost, bool)
        checks["pricing_found_present"] = isinstance(pricing_found, bool)
        checks["non_negative_tokens"] = all(value >= 0 for value in (input_tokens, output_tokens, cached_input_tokens, total_tokens))
        checks["non_negative_costs"] = all(value >= 0 for value in (input_cost, output_cost, cached_input_cost, total_cost))
        checks["total_matches_sum"] = total_cost == round(input_cost + output_cost + cached_input_cost, 6) if all(value >= 0 for value in (input_cost, output_cost, cached_input_cost, total_cost)) else False

        if not provider:
            errors.append("Provider is required.")
        if provider and not model:
            warnings.append("Model is missing for a cost payload.")
        if not currency:
            errors.append("Currency is required.")
        if any(value < 0 for value in (input_tokens, output_tokens, cached_input_tokens, total_tokens)):
            errors.append("Token counts must be non-negative integers.")
        if any(value < 0 for value in (input_cost, output_cost, cached_input_cost, total_cost)):
            errors.append("Cost values must be non-negative numbers.")
        if not checks["estimated_tokens_present"]:
            warnings.append("Estimated token flag is missing or malformed.")
        if not checks["estimated_cost_present"]:
            warnings.append("Estimated cost flag is missing or malformed.")
        if not checks["pricing_found_present"]:
            warnings.append("Pricing found flag is missing or malformed.")
        if pricing_found and not pricing_version:
            errors.append("Pricing version is required when pricing was found.")
        if checks["total_matches_sum"] is False and all(value >= 0 for value in (input_cost, output_cost, cached_input_cost, total_cost)):
            warnings.append("Total cost does not match the sum of cost components.")

        return {"valid": not errors, "warnings": warnings, "errors": errors, "checks": checks}

    def validate_aggregation(self, summary: dict[str, Any]) -> dict[str, Any]:
        """Validate aggregated cost totals."""

        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}

        if not isinstance(summary, dict):
            return {"valid": False, "warnings": [], "errors": ["Aggregation summary must be a dictionary."], "checks": {}}

        for key in ("total_cost", "records_count", "estimated_cost_records", "unknown_pricing_records"):
            checks[f"{key}_valid"] = safe_float(summary.get(key), -1.0) >= 0 if key == "total_cost" else safe_int(summary.get(key), -1) >= 0
            if not checks[f"{key}_valid"]:
                errors.append(f"Invalid aggregation value for {key}.")

        if safe_text(summary.get("currency"), limit=32) == "":
            warnings.append("Aggregation currency is missing.")

        return {"valid": not errors, "warnings": warnings, "errors": errors, "checks": checks}
