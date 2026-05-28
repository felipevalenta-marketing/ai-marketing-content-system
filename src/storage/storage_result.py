"""Structured result builders for storage operations."""

from __future__ import annotations

from typing import Any


def build_success_result(**kwargs: Any) -> dict[str, Any]:
    return {"success": True, **kwargs}


def build_failure_result(*, error: str, **kwargs: Any) -> dict[str, Any]:
    return {"success": False, "error": error, **kwargs}


def build_validation_failure_result(*, errors: list[str], warnings: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
    return {"success": False, "errors": errors, "warnings": warnings or [], **kwargs}


def build_read_result(record: dict[str, Any] | None, *, record_type: str, record_id: str, path: str, warnings: list[str] | None = None, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "success": bool(record),
        "record": record or {},
        "record_type": record_type,
        "record_id": record_id,
        "path": path,
        "warnings": warnings or [],
        "errors": errors or [],
    }


def build_list_result(records: list[dict[str, Any]], *, record_type: str | None = None, warnings: list[str] | None = None, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "record_type": record_type,
        "records": records,
        "count": len(records),
        "warnings": warnings or [],
        "errors": errors or [],
    }
