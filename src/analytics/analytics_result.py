"""Result helpers for analytics outputs."""

from __future__ import annotations

from typing import Any

from src.analytics.analytics_contracts import AnalyticsResultContract
from src.reporting.report_metrics import safe_list, safe_text


def _normalize_text_list(values: list[Any] | None) -> list[str]:
    items = []
    for value in safe_list(values):
        text = safe_text(value, limit=240)
        if text:
            items.append(text)
    return list(dict.fromkeys(items))


def build_success_result(**kwargs: Any) -> dict[str, Any]:
    result = AnalyticsResultContract(success=True, analytics_type=safe_text(kwargs.get("analytics_type"), limit=80)).to_dict()
    result.update(kwargs)
    result["success"] = True
    return result


def build_empty_result(**kwargs: Any) -> dict[str, Any]:
    result = AnalyticsResultContract(success=True, analytics_type=safe_text(kwargs.get("analytics_type"), limit=80)).to_dict()
    result.update(kwargs)
    result["success"] = True
    result.setdefault("insights", [])
    result.setdefault("recommendations", [])
    return result


def build_failure_result(error: str, **kwargs: Any) -> dict[str, Any]:
    result = AnalyticsResultContract(success=False, analytics_type=safe_text(kwargs.get("analytics_type"), limit=80)).to_dict()
    result.update(kwargs)
    result["success"] = False
    result.setdefault("errors", [])
    if error:
        result["errors"] = _normalize_text_list(list(result["errors"]) + [error])
    return result


def build_dashboard_payload_result(**kwargs: Any) -> dict[str, Any]:
    result = build_success_result(**kwargs)
    result["dashboard_payload"] = kwargs.get("dashboard_payload", {})
    return result


def normalize_warnings(values: list[Any] | None) -> list[str]:
    return _normalize_text_list(values)


def normalize_errors(values: list[Any] | None) -> list[str]:
    return _normalize_text_list(values)

