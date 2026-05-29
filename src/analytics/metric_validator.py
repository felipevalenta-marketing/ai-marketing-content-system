"""Validation helpers for analytics outputs."""

from __future__ import annotations

from typing import Any
import json

from src.analytics.analytics_contracts import SUPPORTED_ANALYTICS_TYPES
from src.reporting.report_metrics import safe_float, safe_list, safe_text


SECRET_MARKERS = ("openai_api_key", "api_key", "password", "secret", "bearer", ".env", "sk-")


class MetricValidator:
    def validate(self, analytics: dict[str, Any]) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []

        analytics_type = safe_text(analytics.get("analytics_type"), limit=80)
        if not analytics_type:
            errors.append("analytics_type is required.")
        elif analytics_type not in SUPPORTED_ANALYTICS_TYPES:
            errors.append(f"Unsupported analytics_type: {analytics_type}")

        date_range = analytics.get("date_range")
        if date_range is not None and not isinstance(date_range, dict):
            errors.append("date_range must be an object with start/end values.")

        filters = analytics.get("filters")
        if filters is not None and not isinstance(filters, dict):
            errors.append("filters must be an object.")

        self._validate_numeric_block(analytics.get("kpis"), warnings, errors)
        self._validate_numeric_block(analytics.get("sections"), warnings, errors)
        self._validate_numeric_block(analytics.get("trends"), warnings, errors)

        try:
            serialized = json.dumps(analytics, default=str, ensure_ascii=False)
            if any(marker in serialized.lower() for marker in SECRET_MARKERS):
                errors.append("Analytics output contains secret-like content.")
        except Exception as exc:
            errors.append(f"Analytics payload is not serializable: {exc}")

        return {"valid": not errors, "warnings": warnings, "errors": errors}

    def _validate_numeric_block(self, value: Any, warnings: list[str], errors: list[str]) -> None:
        if not isinstance(value, dict):
            return
        for key, item in value.items():
            if isinstance(item, dict):
                if {"label", "value", "status"}.issubset(set(item.keys())) and "unit" in item:
                    self._validate_kpi(item, warnings, errors)
                self._validate_numeric_block(item, warnings, errors)
                continue
            if isinstance(item, (int, float)):
                if item < 0:
                    errors.append("Numeric analytics values must be non-negative.")
            if isinstance(item, str):
                if item.endswith("%"):
                    try:
                        percentage = float(item.rstrip("%"))
                        if not 0 <= percentage <= 100:
                            errors.append("Percentage values must be between 0 and 100.")
                    except ValueError:
                        warnings.append(f"Unable to parse percentage value: {item}")

    def _validate_kpi(self, kpi: dict[str, Any], warnings: list[str], errors: list[str]) -> None:
        value = kpi.get("value")
        unit = safe_text(kpi.get("unit"), limit=16)
        if isinstance(value, (int, float)) and value < 0:
            errors.append("KPI values must be non-negative.")
        if unit == "%" and isinstance(value, (int, float)) and not 0 <= value <= 100:
            errors.append("KPI percentages must be between 0 and 100.")
