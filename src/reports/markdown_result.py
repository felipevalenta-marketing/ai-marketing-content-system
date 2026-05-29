"""Markdown report result helpers."""

from __future__ import annotations

from typing import Any


def build_success_result(**kwargs: Any) -> dict[str, Any]:
    return {"success": True, "warnings": [], "errors": [], **kwargs}


def build_failure_result(*, error: str, **kwargs: Any) -> dict[str, Any]:
    errors = list(kwargs.pop("errors", []))
    if error:
        errors.append(error)
    return {"success": False, "warnings": list(kwargs.pop("warnings", [])), "errors": errors, **kwargs}


def build_validation_failure_result(*, errors: list[str], warnings: list[str] | None = None, **kwargs: Any) -> dict[str, Any]:
    return {"success": False, "warnings": warnings or [], "errors": list(errors), **kwargs}


def build_export_result(*, path: str, markdown: str, metadata: dict[str, Any] | None = None, warnings: list[str] | None = None, errors: list[str] | None = None) -> dict[str, Any]:
    return {
        "success": not bool(errors),
        "path": path,
        "markdown": markdown,
        "metadata": metadata or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }

