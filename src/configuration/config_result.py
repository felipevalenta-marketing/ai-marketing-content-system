"""Structured configuration results."""

from __future__ import annotations

from typing import Any


def _normalize_strings(values: list[str] | None) -> list[str]:
    return [str(item) for item in list(values or []) if str(item)]


def build_success_result(*, data: dict[str, Any] | None = None, warnings: list[str] | None = None, errors: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": dict(data or {}), "warnings": _normalize_strings(warnings), "errors": _normalize_strings(errors), "metadata": dict(metadata or {})}


def build_validation_result(*, valid: bool, warnings: list[str] | None = None, errors: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": bool(valid), "valid": bool(valid), "warnings": _normalize_strings(warnings), "errors": _normalize_strings(errors), "metadata": dict(metadata or {})}


def build_update_result(*, flag: str = "", value: bool | None = None, warnings: list[str] | None = None, errors: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": not errors, "flag": flag, "value": value, "warnings": _normalize_strings(warnings), "errors": _normalize_strings(errors), "metadata": dict(metadata or {})}


def build_summary_result(*, summary: dict[str, Any] | None = None, warnings: list[str] | None = None, errors: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": not errors, "summary": dict(summary or {}), "warnings": _normalize_strings(warnings), "errors": _normalize_strings(errors), "metadata": dict(metadata or {})}

