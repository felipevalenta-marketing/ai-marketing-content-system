"""Permission checking helpers."""

from __future__ import annotations

from typing import Any

from src.rbac.permission_registry import is_valid_permission, normalize_permission_name
from src.rbac.role_registry import get_role, is_valid_role, normalize_role_name
from src.rbac.rbac_result import build_permission_allowed_result, build_permission_denied_result


def _user_role(user: dict[str, Any] | None) -> str:
    role = normalize_role_name((user or {}).get("role", "viewer"))
    return role if is_valid_role(role) else "disabled"


def _user_permissions(user: dict[str, Any] | None) -> list[str]:
    permissions = (user or {}).get("permissions", [])
    if isinstance(permissions, list):
        return [normalize_permission_name(item) for item in permissions if normalize_permission_name(item)]
    return []


def check_permission(user: dict[str, Any] | None, permission: str) -> dict[str, Any]:
    normalized_permission = normalize_permission_name(permission)
    role_name = _user_role(user)
    if not normalized_permission or not is_valid_permission(normalized_permission):
        return build_permission_denied_result(normalized_permission, role_name, reason="Invalid permission.", errors=["Invalid permission."])
    if role_name == "disabled":
        return build_permission_denied_result(normalized_permission, role_name, reason="Disabled users have no access.", errors=["Disabled users have no access."])
    role = get_role(role_name)
    if role_name == "admin" or "admin:all" in _user_permissions(user) or normalized_permission in _user_permissions(user):
        return build_permission_allowed_result(normalized_permission, role_name, metadata={"role_level": role.get("level", 0)})
    if normalized_permission in role.get("permissions", []):
        return build_permission_allowed_result(normalized_permission, role_name, metadata={"role_level": role.get("level", 0)})
    return build_permission_denied_result(normalized_permission, role_name, reason="Forbidden.", errors=["Forbidden."])
