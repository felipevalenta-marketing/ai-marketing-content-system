"""Organization result builders."""

from __future__ import annotations

from typing import Any


def _normalize(values: list[Any] | None) -> list[str]:
    return [str(item) for item in list(values or []) if str(item)]


def build_organization_success(data: dict[str, Any] | None = None, warnings: list[Any] | None = None, errors: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": dict(data or {}), "warnings": _normalize(warnings), "errors": _normalize(errors), "metadata": dict(metadata or {})}


def build_organization_failure(message: str, warnings: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "data": {}, "warnings": _normalize(warnings), "errors": [str(message)], "metadata": dict(metadata or {})}


def build_validation_failure(errors: list[Any] | None = None, warnings: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "valid": False, "data": {}, "warnings": _normalize(warnings), "errors": _normalize(errors), "metadata": dict(metadata or {})}

