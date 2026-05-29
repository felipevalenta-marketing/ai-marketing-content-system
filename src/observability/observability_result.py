"""Observability result builders."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_list, safe_text


def build_success_result(*, data: Any | None = None, warnings: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": data, "warnings": [safe_text(item, limit=240) for item in safe_list(warnings)], "errors": [], "metadata": metadata or {}}


def build_failure_result(*, errors: list[Any] | None = None, warnings: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "data": None, "warnings": [safe_text(item, limit=240) for item in safe_list(warnings)], "errors": [safe_text(item, limit=240) for item in safe_list(errors)], "metadata": metadata or {}}


def build_health_result(data: dict[str, Any], *, warnings: list[Any] | None = None, errors: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": data, "warnings": [safe_text(item, limit=240) for item in safe_list(warnings)], "errors": [safe_text(item, limit=240) for item in safe_list(errors)], "metadata": metadata or {}}

