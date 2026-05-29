"""Structured RBAC results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_permission_allowed_result(permission: str, role: str, *, reason: str = "Allowed.", warnings: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"allowed": True, "permission": permission, "role": role, "reason": reason, "warnings": list(warnings or []), "errors": [], "metadata": dict(metadata or {})}


def build_permission_denied_result(permission: str, role: str, *, reason: str = "Forbidden.", warnings: list[str] | None = None, errors: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"allowed": False, "permission": permission, "role": role, "reason": reason, "warnings": list(warnings or []), "errors": list(errors or [reason]), "metadata": dict(metadata or {})}


def build_role_assignment_result(*, success: bool, user: dict[str, Any] | None = None, warnings: list[str] | None = None, errors: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": bool(success), "user": user or {}, "warnings": list(warnings or []), "errors": list(errors or []), "metadata": dict(metadata or {})}


def build_access_summary_result(
    *,
    role: str = "",
    role_label: str = "",
    role_type: str = "",
    role_level: int = 0,
    role_hierarchy: list[dict[str, Any]] | None = None,
    permissions: list[str] | None = None,
    permission_domains: list[dict[str, Any]] | None = None,
    access: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "role": role,
        "role_label": role_label,
        "role_type": role_type,
        "role_level": int(role_level or 0),
        "role_hierarchy": list(role_hierarchy or []),
        "permissions": list(permissions or []),
        "permission_domains": list(permission_domains or []),
        "access": dict(access or {}),
        "summary": dict(summary or {}),
        "warnings": list(warnings or []),
        "errors": list(errors or []),
        "metadata": dict(metadata or {}),
    }


def build_audit_metadata(*, actor_user_id: str = "", actor_role: str = "", action: str = "", target_id: str = "", resource: str = "", details: dict[str, Any] | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "created_at": now,
        "updated_at": now,
        "created_by": actor_user_id or "system",
        "updated_by": actor_user_id or "system",
        "actor_user_id": actor_user_id,
        "actor_role": actor_role,
        "action": action,
        "resource": resource,
        "target_id": target_id,
        "details": dict(details or {}),
    }


def build_rbac_health_result(*, health_score: int = 0, status: str = "critical", warnings: list[str] | None = None, errors: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "health_score": max(0, min(100, int(health_score or 0))),
        "status": status,
        "warnings": list(warnings or []),
        "errors": list(errors or []),
        "metadata": dict(metadata or {}),
    }
