"""Input sanitization helpers."""

from __future__ import annotations

from typing import Any
import re

from src.reports.markdown_utils import safe_text


SCRIPT_PATTERNS = (
    re.compile(r"<\s*script\b", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"onerror\s*=", re.IGNORECASE),
    re.compile(r"onload\s*=", re.IGNORECASE),
)


def sanitize_string(value: Any, *, limit: int = 2000) -> dict[str, Any]:
    text = safe_text(value, limit=limit)
    warnings: list[str] = []
    errors: list[str] = []
    if any(pattern.search(text) for pattern in SCRIPT_PATTERNS):
        errors.append("Potential script injection detected.")
        text = re.sub(r"<\s*script\b.*?<\s*/\s*script\s*>", "[removed-script]", text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r"javascript\s*:", "", text, flags=re.IGNORECASE)
        text = re.sub(r"onerror\s*=\s*[^>\s]+", "", text, flags=re.IGNORECASE)
        text = re.sub(r"onload\s*=\s*[^>\s]+", "", text, flags=re.IGNORECASE)
    return {"value": text, "warnings": warnings, "errors": errors}


def sanitize_input(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        warnings: list[str] = []
        errors: list[str] = []
        for key, item in value.items():
            result = sanitize_input(item)
            sanitized[str(key)] = result.get("value")
            warnings.extend(result.get("warnings", []))
            errors.extend(result.get("errors", []))
        return {"value": sanitized, "warnings": warnings, "errors": errors}
    if isinstance(value, list):
        warnings: list[str] = []
        errors: list[str] = []
        sanitized_items = []
        for item in value:
            result = sanitize_input(item)
            sanitized_items.append(result.get("value"))
            warnings.extend(result.get("warnings", []))
            errors.extend(result.get("errors", []))
        return {"value": sanitized_items, "warnings": warnings, "errors": errors}
    return sanitize_string(value)


def sanitize_request_params(params: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(params, dict):
        return {"value": {}, "warnings": [], "errors": []}
    sanitized: dict[str, Any] = {}
    warnings: list[str] = []
    errors: list[str] = []
    for key, value in params.items():
        result = sanitize_input(value)
        sanitized[str(key)] = result.get("value")
        warnings.extend(result.get("warnings", []))
        errors.extend(result.get("errors", []))
    return {"value": sanitized, "warnings": warnings, "errors": errors}


def validate_input(value: Any) -> dict[str, Any]:
    result = sanitize_input(value)
    return {"valid": not result.get("errors"), "warnings": result.get("warnings", []), "errors": result.get("errors", []), "value": result.get("value")}
