"""Standard API response helpers."""

from __future__ import annotations

from typing import Any

from src.api.sanitizer import sanitize_api_payload
from src.reports.markdown_utils import safe_list, safe_text


def build_api_response(
    *,
    success: bool,
    data: Any | None = None,
    warnings: list[Any] | None = None,
    errors: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": bool(success),
        "data": sanitize_api_payload(data) if data is not None else None,
        "warnings": [safe_text(item, limit=240) for item in safe_list(warnings)],
        "errors": [safe_text(item, limit=240) for item in safe_list(errors)],
        "metadata": sanitize_api_payload(metadata or {}),
    }


def build_api_error(message: str, *, metadata: dict[str, Any] | None = None, warnings: list[Any] | None = None, status_code: int = 400) -> tuple[dict[str, Any], int]:
    return build_api_response(success=False, data=None, warnings=warnings, errors=[message], metadata=metadata), int(status_code)
