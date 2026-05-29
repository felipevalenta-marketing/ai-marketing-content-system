"""RBAC orchestration."""

from __future__ import annotations

from typing import Any

from src.rbac.permission_checker import check_permission
from src.rbac.permission_registry import is_valid_permission, list_permission_domains, list_permissions, normalize_permission_name, permissions_by_domain
from src.rbac.rbac_result import build_access_summary_result, build_audit_metadata, build_rbac_health_result, build_role_assignment_result
from src.rbac.rbac_validator import validate_role_assignment, validate_rbac_configuration
from src.rbac.role_registry import get_role, get_role_hierarchy, get_role_level, is_valid_role, list_roles, normalize_role_name
from src.users.user_manager import UserManager


class RBACManager:
    def __init__(self, user_manager: UserManager, logger: Any | None = None) -> None:
        self.user_manager = user_manager
        self.logger = logger

    def get_user_role(self, user: dict[str, Any]) -> str:
        role = normalize_role_name((user or {}).get("role", "viewer")) or "viewer"
        if not is_valid_role(role):
            return "disabled"
        return role

    def get_user_permissions(self, user: dict[str, Any]) -> list[str]:
        role = self.get_user_role(user)
        if role == "admin":
            return [item["permission"] for item in list_permissions()]
        if role == "disabled":
            return []
        profile = get_role(role)
        permissions = [permission for permission in list(profile.get("permissions", [])) if is_valid_permission(permission)]
        explicit = (user or {}).get("permissions", [])
        if isinstance(explicit, list):
            permissions.extend(normalize_permission_name(item) for item in explicit if normalize_permission_name(item) and is_valid_permission(normalize_permission_name(item)))
        if "admin:all" in permissions:
            return [item["permission"] for item in list_permissions()]
        return sorted({normalize_permission_name(permission) for permission in permissions if normalize_permission_name(permission)})

    def has_permission(self, user: dict[str, Any], permission: str) -> bool:
        return bool(check_permission({"role": self.get_user_role(user), "permissions": self.get_user_permissions(user)}, permission).get("allowed"))

    def has_any_permission(self, user: dict[str, Any], permissions: list[str]) -> bool:
        return any(self.has_permission(user, permission) for permission in permissions)

    def has_all_permissions(self, user: dict[str, Any], permissions: list[str]) -> bool:
        return all(self.has_permission(user, permission) for permission in permissions)

    def assign_role(self, user_id: str, role: str, actor: dict[str, Any] | None = None) -> dict[str, Any]:
        validation = validate_role_assignment(actor, role, str((actor or {}).get("user_id", "")), user_id)
        if not validation["valid"]:
            return build_role_assignment_result(success=False, user={}, warnings=validation["warnings"], errors=validation["errors"], metadata={"validation": validation})
        updated = self.user_manager.update_user(user_id, {"role": normalize_role_name(role)}, updated_by=str((actor or {}).get("user_id", "")), allow_role=True)
        return build_role_assignment_result(success=bool(updated.get("success", False)), user=updated.get("user", {}), warnings=updated.get("warnings", []), errors=updated.get("errors", []), metadata={"validation": validation})

    def list_roles(self) -> dict[str, Any]:
        hierarchy = get_role_hierarchy()
        return {
            "success": True,
            "roles": list_roles(),
            "hierarchy": hierarchy,
            "warnings": [],
            "errors": [],
            "metadata": {"role_count": len(hierarchy)},
        }

    def list_permissions(self) -> dict[str, Any]:
        grouped = permissions_by_domain()
        domains = list_permission_domains()
        permissions = list_permissions()
        return {
            "success": True,
            "permissions": permissions,
            "grouped": grouped,
            "domains": domains,
            "warnings": [],
            "errors": [],
            "metadata": {"permission_count": len(permissions), "domain_count": len(domains)},
        }

    def build_access_summary(self, user: dict[str, Any]) -> dict[str, Any]:
        role = self.get_user_role(user)
        permissions = self.get_user_permissions(user)
        role_meta = get_role(role)
        all_permissions = [item["permission"] for item in list_permissions()]
        access = {permission: self.has_permission(user, permission) for permission in all_permissions}
        domain_lookup = {str(domain.get("domain", "")): dict(domain) for domain in list_permission_domains()}
        domain_breakdown: list[dict[str, Any]] = []
        for domain, domain_permissions in permissions_by_domain().items():
            allowed_permissions = [permission.get("permission") for permission in domain_permissions if access.get(permission.get("permission", ""), False)]
            domain_breakdown.append(
                {
                    "domain": domain,
                    "label": str(domain_lookup.get(domain, {}).get("label", domain.title())),
                    "description": str(domain_lookup.get(domain, {}).get("description", "")),
                    "total": len(domain_permissions),
                    "allowed": len(allowed_permissions),
                    "permissions": [permission.get("permission") for permission in domain_permissions],
                    "allowed_permissions": allowed_permissions,
                }
            )
        summary = {
            "allowed_permissions_count": sum(1 for allowed in access.values() if allowed),
            "total_permissions_count": len(all_permissions),
            "allowed_domains_count": sum(1 for item in domain_breakdown if item["allowed"]),
            "total_domains_count": len(domain_breakdown),
            "can_manage_system": access.get("system:read", False) or access.get("system:manage", False) or access.get("admin:all", False),
            "can_manage_users": access.get("user:manage", False) or access.get("admin:all", False),
        }
        metadata = {
            "user_id": user.get("user_id", ""),
            "role_metadata": role_meta,
            "audit": build_audit_metadata(
                actor_user_id=str(user.get("user_id", "")),
                actor_role=role,
                action="access_summary",
                target_id=str(user.get("user_id", "")),
                resource="rbac",
                details={"role": role},
            ),
        }
        return build_access_summary_result(
            role=role,
            role_label=str(role_meta.get("label", role.title() or "Viewer")),
            role_type=str(role_meta.get("type", "system")),
            role_level=get_role_level(role),
            role_hierarchy=get_role_hierarchy(),
            permissions=permissions,
            permission_domains=domain_breakdown,
            access=access,
            summary=summary,
            metadata=metadata,
        )

    def validate_configuration(self) -> dict[str, Any]:
        return validate_rbac_configuration()

    def get_health(self) -> dict[str, Any]:
        validation = self.validate_configuration()
        role_count = len(list_roles())
        permissions = list_permissions()
        domain_count = len(list_permission_domains())
        warnings = list(validation.get("warnings", []))
        errors = list(validation.get("errors", []))
        health_score = 100
        health_score -= len(errors) * 25
        health_score -= len(warnings) * 5
        if role_count < 5:
            warnings.append("Role registry appears incomplete.")
            health_score -= 5
        if not permissions:
            errors.append("Permission registry is empty.")
            health_score = 0
        health_score = max(0, min(100, health_score))
        if errors:
            status = "critical"
        elif warnings or health_score < 80:
            status = "warning"
        else:
            status = "healthy"
        return build_rbac_health_result(
            health_score=health_score,
            status=status,
            warnings=warnings,
            errors=errors,
            metadata={
                "role_count": role_count,
                "permission_count": len(permissions),
                "domain_count": domain_count,
                "configuration_valid": bool(validation.get("valid", False)),
            },
        )
