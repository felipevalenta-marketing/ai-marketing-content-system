"""Shared observability context helpers."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from .log_sanitizer import redact_log_payload


_OBSERVABILITY_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("observability_context", default={})


def build_context(
    *,
    request_context: dict[str, Any] | None = None,
    user_context: dict[str, Any] | None = None,
    organization_context: dict[str, Any] | None = None,
    team_context: dict[str, Any] | None = None,
    workflow_context: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = {
        "request": redact_log_payload(dict(request_context or {})),
        "user": redact_log_payload(dict(user_context or {})),
        "organization": redact_log_payload(dict(organization_context or {})),
        "team": redact_log_payload(dict(team_context or {})),
        "workflow": redact_log_payload(dict(workflow_context or {})),
        "metadata": redact_log_payload(dict(metadata or {})),
    }
    sanitized = sanitize_context(context)
    _OBSERVABILITY_CONTEXT.set(sanitized)
    return sanitized


def get_context() -> dict[str, Any]:
    return sanitize_context(dict(_OBSERVABILITY_CONTEXT.get() or {}))


def sanitize_context(context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(context, dict):
        return {}
    sanitized: dict[str, Any] = {}
    for key, value in context.items():
        sanitized[str(key)] = redact_log_payload(value)
    return sanitized


def clear_context() -> None:
    _OBSERVABILITY_CONTEXT.set({})
