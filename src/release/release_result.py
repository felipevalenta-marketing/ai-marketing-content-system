"""Result builders for the release layer."""

from __future__ import annotations

from typing import Any


def _clean_list(values: list[Any] | None) -> list[str]:
    return [str(value) for value in list(values or []) if str(value)]


def build_release_success_result(*, data: dict[str, Any] | None = None, warnings: list[Any] | None = None, errors: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": True, "data": dict(data or {}), "warnings": _clean_list(warnings), "errors": _clean_list(errors), "metadata": dict(metadata or {})}


def build_release_failure_result(*, errors: list[Any] | None = None, warnings: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "data": {}, "warnings": _clean_list(warnings), "errors": _clean_list(errors), "metadata": dict(metadata or {})}


def build_release_health_result(*, data: dict[str, Any] | None = None, warnings: list[Any] | None = None, errors: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_release_success_result(data=data, warnings=warnings, errors=errors, metadata=metadata)


def build_release_score_result(*, release_score: int, release_status: str, recommendations: list[Any] | None = None, warnings: list[Any] | None = None, errors: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": not errors,
        "release_score": int(release_score),
        "release_status": str(release_status),
        "recommendations": _clean_list(recommendations),
        "warnings": _clean_list(warnings),
        "errors": _clean_list(errors),
        "metadata": dict(metadata or {}),
    }


def build_release_certification_result(*, mvp_certified: bool, production_ready: bool, certification_status: str, version: str, warnings: list[Any] | None = None, errors: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": not errors,
        "mvp_certified": bool(mvp_certified),
        "production_ready": bool(production_ready),
        "certification_status": str(certification_status),
        "version": str(version),
        "warnings": _clean_list(warnings),
        "errors": _clean_list(errors),
        "metadata": dict(metadata or {}),
    }


def build_release_maturity_result(*, maturity_score: int, maturity_level: str, warnings: list[Any] | None = None, recommendations: list[Any] | None = None, errors: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": not errors,
        "maturity_score": int(maturity_score),
        "maturity_level": str(maturity_level),
        "warnings": _clean_list(warnings),
        "recommendations": _clean_list(recommendations),
        "errors": _clean_list(errors),
        "metadata": dict(metadata or {}),
    }


def build_release_governance_result(*, governance_status: str, warnings: list[Any] | None = None, blocked_reasons: list[Any] | None = None, errors: list[Any] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": not errors,
        "governance_status": str(governance_status),
        "release_blocked": str(governance_status).lower() == "blocked",
        "release_warning": str(governance_status).lower() == "warning",
        "approval_recommended": str(governance_status).lower() == "approved",
        "warnings": _clean_list(warnings),
        "blocked_reasons": _clean_list(blocked_reasons),
        "errors": _clean_list(errors),
        "metadata": dict(metadata or {}),
    }
