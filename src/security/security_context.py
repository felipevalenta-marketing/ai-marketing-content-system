"""Security context helpers."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from src.observability.observability_context import build_context as build_observability_context
from src.observability.observability_context import get_context as get_observability_context
from src.observability.observability_context import sanitize_context as sanitize_observability_context
from src.observability.log_sanitizer import redact_log_payload


_SECURITY_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("security_context", default={})


def build_context(
    *,
    request_context: dict[str, Any] | None = None,
    auth_context: dict[str, Any] | None = None,
    rbac_context: dict[str, Any] | None = None,
    organization_context: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = {
        "request": redact_log_payload(dict(request_context or {})),
        "auth": redact_log_payload(dict(auth_context or {})),
        "rbac": redact_log_payload(dict(rbac_context or {})),
        "organization": redact_log_payload(dict(organization_context or {})),
        "metadata": redact_log_payload(dict(metadata or {})),
    }
    sanitized = sanitize_context(context)
    _SECURITY_CONTEXT.set(sanitized)
    build_observability_context(
        request_context=dict(request_context or {}),
        user_context=dict(auth_context or {}),
        organization_context=dict(organization_context or {}),
        metadata=dict(metadata or {}),
    )
    return sanitized


def get_context() -> dict[str, Any]:
    current = dict(_SECURITY_CONTEXT.get() or {})
    if current:
        return sanitize_context(current)
    return sanitize_observability_context(get_observability_context())


def sanitize_context(context: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(context, dict):
        return {}
    return {str(key): redact_log_payload(value) for key, value in context.items()}


def validate_context(context: dict[str, Any] | None) -> dict[str, Any]:
    sanitized = sanitize_context(context)
    warnings: list[str] = []
    errors: list[str] = []
    if not isinstance(context, dict):
        errors.append("Context must be a dictionary.")
    if any("secret" in str(key).lower() for key in sanitized.keys()):
        warnings.append("Potential secret-like context key detected.")
    return {"valid": not errors, "warnings": warnings, "errors": errors, "context": sanitized}

