"""Standard result helpers for security operations."""

from __future__ import annotations

from typing import Any


def _normalize_messages(values: list[Any] | None) -> list[str]:
    return [str(item).strip() for item in list(values or []) if str(item).strip()]


def build_success_result(
    *,
    data: dict[str, Any] | None = None,
    warnings: list[Any] | None = None,
    errors: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "data": dict(data or {}),
        "warnings": _normalize_messages(warnings),
        "errors": _normalize_messages(errors),
        "metadata": dict(metadata or {}),
    }


def build_failure_result(
    *,
    data: dict[str, Any] | None = None,
    warnings: list[Any] | None = None,
    errors: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "data": dict(data or {}),
        "warnings": _normalize_messages(warnings),
        "errors": _normalize_messages(errors),
        "metadata": dict(metadata or {}),
    }


def build_health_result(
    *,
    security_score: int = 0,
    security_status: str = "critical",
    warnings: list[Any] | None = None,
    recommendations: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "security_score": max(0, min(100, int(security_score or 0))),
        "security_status": str(security_status or "critical"),
        "warnings": _normalize_messages(warnings),
        "recommendations": _normalize_messages(recommendations),
        "metadata": dict(metadata or {}),
    }


def build_findings_result(
    *,
    findings: list[dict[str, Any]] | None = None,
    warnings: list[Any] | None = None,
    errors: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_success_result(
        data={"findings": list(findings or []), "count": len(list(findings or []))},
        warnings=warnings,
        errors=errors,
        metadata=metadata,
    )


def build_dependency_result(
    *,
    dependencies_valid: bool,
    warnings: list[Any] | None = None,
    errors: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_success_result(
        data={"dependencies_valid": bool(dependencies_valid)},
        warnings=warnings,
        errors=errors,
        metadata=metadata,
    )

