"""RBAC validation helpers."""

from __future__ import annotations

from typing import Any

from src.rbac.permission_registry import is_valid_permission, list_permissions, normalize_permission_name
from src.rbac.role_registry import get_role, get_role_level, is_valid_role, list_roles, normalize_role_name, role_has_at_least


def validate_rbac_configuration() -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    for role in list_roles():
        role_name = normalize_role_name(role.get("role", ""))
        if not is_valid_role(role_name):
            errors.append(f"Unknown role: {role_name}")
            continue
        if role_name == "disabled" and role.get("permissions"):
            errors.append("Disabled role must not have permissions.")
        if not role.get("type"):
            warnings.append(f"Role metadata missing type for: {role_name}")
        if role_name != "disabled" and not isinstance(role.get("inherits_from"), list):
            warnings.append(f"Role hierarchy metadata missing for: {role_name}")
        for permission in role.get("permissions", []):
            if not is_valid_permission(permission):
                errors.append(f"Unknown permission in role mapping: {permission}")
    for permission in list_permissions():
        if not is_valid_permission(permission.get("permission", "")):
            errors.append(f"Unknown permission: {permission.get('permission', '')}")
    return {"valid": not errors, "warnings": warnings, "errors": errors}


def validate_user_role(role: str) -> dict[str, Any]:
    normalized = normalize_role_name(role)
    if not is_valid_role(normalized):
        return {"valid": False, "warnings": [], "errors": ["Invalid role."]}
    return {"valid": True, "warnings": [], "errors": []}


def validate_role_assignment(actor: dict[str, Any] | None, target_role: str, current_user_id: str, target_user_id: str) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized = normalize_role_name(target_role)
    if not is_valid_role(normalized):
        errors.append("Invalid role.")
    actor_role = normalize_role_name((actor or {}).get("role", "disabled"))
    actor_permissions = set((actor or {}).get("permissions", []) or [])
    actor_permissions.update(get_role(actor_role).get("permissions", []))
    actor_level = get_role_level(actor_role)
    target_level = get_role_level(normalized) if is_valid_role(normalized) else 0
    if actor_role == "disabled":
        errors.append("Disabled users cannot assign roles.")
    if "admin:all" not in actor_permissions and "user:manage" not in actor_permissions:
        errors.append("Insufficient permission to assign roles.")
    if current_user_id == target_user_id and actor_role != "admin":
        errors.append("Self role assignment is restricted.")
    if actor_role != "admin" and not role_has_at_least(actor_role, normalized):
        errors.append("Cannot assign a role higher than your own.")
    if actor_role == "admin" and target_level > actor_level:
        warnings.append("Admin role assignment exceeds standard hierarchy; continuing due to admin override.")
    return {"valid": not errors, "warnings": warnings, "errors": errors}
