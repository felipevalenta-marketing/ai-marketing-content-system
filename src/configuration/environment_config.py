"""Environment-aware configuration helpers."""

from __future__ import annotations

from typing import Any
import os


def normalize_environment(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"development", "staging", "production"}:
        return normalized
    return "development"


def build_environment_config(environment: str | None = None) -> dict[str, Any]:
    resolved = normalize_environment(environment or os.getenv("APP_ENV", "development"))
    if resolved == "production":
        return {"environment": resolved, "debug": False, "show_stack_traces": False}
    if resolved == "staging":
        return {"environment": resolved, "debug": True, "show_stack_traces": False}
    return {"environment": resolved, "debug": True, "show_stack_traces": True}

