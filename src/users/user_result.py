"""Structured user results."""

from __future__ import annotations

from typing import Any


def build_success_result(*, user: dict[str, Any] | None = None, warnings: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "user": user or {}, "warnings": list(warnings or []), "errors": [], "metadata": dict(metadata or {})}


def build_failure_result(message: str, *, user: dict[str, Any] | None = None, warnings: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "user": user or {}, "warnings": list(warnings or []), "errors": [message], "metadata": dict(metadata or {})}
