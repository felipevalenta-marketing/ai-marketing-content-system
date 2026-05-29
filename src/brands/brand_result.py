"""Result helpers for brand operations."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_list, safe_text


def build_success_result(**kwargs: Any) -> dict[str, Any]:
    result = {"success": True, "warnings": [], "errors": []}
    result.update(kwargs)
    result["success"] = True
    result["warnings"] = _normalize_strings(result.get("warnings"))
    result["errors"] = _normalize_strings(result.get("errors"))
    return result


def build_failure_result(error: str, **kwargs: Any) -> dict[str, Any]:
    result = {"success": False, "warnings": [], "errors": []}
    result.update(kwargs)
    if error:
        result["errors"] = _normalize_strings(list(result.get("errors", [])) + [error])
    return result


def build_not_found_result(brand_id: str, **kwargs: Any) -> dict[str, Any]:
    return build_failure_result(f"Brand not found: {brand_id}", brand_id=brand_id, **kwargs)


def build_validation_result(validation: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    result = {"success": bool(validation.get("valid", False)), **validation}
    result.update(kwargs)
    result["warnings"] = _normalize_strings(result.get("warnings"))
    result["errors"] = _normalize_strings(result.get("errors"))
    return result


def _normalize_strings(values: Any) -> list[str]:
    return [text for text in (safe_text(item, limit=240) for item in safe_list(values)) if text]
