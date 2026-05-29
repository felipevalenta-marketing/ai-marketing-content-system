"""Default permission registry."""

from __future__ import annotations

from typing import Any


PERMISSION_REGISTRY: dict[str, dict[str, Any]] = {
    "generation:read": {"permission": "generation:read", "domain": "generation", "label": "Read generations", "description": ""},
    "generation:create": {"permission": "generation:create", "domain": "generation", "label": "Create generations", "description": ""},
    "workflow:read": {"permission": "workflow:read", "domain": "workflow", "label": "Read workflows", "description": ""},
    "workflow:run": {"permission": "workflow:run", "domain": "workflow", "label": "Run workflows", "description": ""},
    "campaign:read": {"permission": "campaign:read", "domain": "campaign", "label": "Read campaigns", "description": ""},
    "campaign:create": {"permission": "campaign:create", "domain": "campaign", "label": "Create campaigns", "description": ""},
    "asset:read": {"permission": "asset:read", "domain": "asset", "label": "Read assets", "description": ""},
    "asset:create": {"permission": "asset:create", "domain": "asset", "label": "Create assets", "description": ""},
    "report:read": {"permission": "report:read", "domain": "report", "label": "Read reports", "description": ""},
    "report:create": {"permission": "report:create", "domain": "report", "label": "Create reports", "description": ""},
    "report:export": {"permission": "report:export", "domain": "report", "label": "Export reports", "description": ""},
    "storage:read": {"permission": "storage:read", "domain": "storage", "label": "Read storage", "description": ""},
    "storage:write": {"permission": "storage:write", "domain": "storage", "label": "Write storage", "description": ""},
    "analytics:read": {"permission": "analytics:read", "domain": "analytics", "label": "Read analytics", "description": ""},
    "brand:read": {"permission": "brand:read", "domain": "brand", "label": "Read brands", "description": ""},
    "brand:manage": {"permission": "brand:manage", "domain": "brand", "label": "Manage brands", "description": ""},
    "user:read": {"permission": "user:read", "domain": "user", "label": "Read users", "description": ""},
    "user:manage": {"permission": "user:manage", "domain": "user", "label": "Manage users", "description": ""},
    "system:read": {"permission": "system:read", "domain": "system", "label": "Read system configuration", "description": ""},
    "system:manage": {"permission": "system:manage", "domain": "system", "label": "Manage system", "description": ""},
    "admin:all": {"permission": "admin:all", "domain": "admin", "label": "Full access", "description": "Grants all permissions."},
}

PERMISSION_DOMAINS: dict[str, dict[str, Any]] = {
    "generation": {"domain": "generation", "label": "Generation", "description": "Content generation and creation controls."},
    "workflow": {"domain": "workflow", "label": "Workflow", "description": "Workflow orchestration and execution controls."},
    "campaign": {"domain": "campaign", "label": "Campaign", "description": "Campaign composition controls."},
    "asset": {"domain": "asset", "label": "Assets", "description": "Asset coordination and creation controls."},
    "report": {"domain": "report", "label": "Reports", "description": "Report creation and export controls."},
    "storage": {"domain": "storage", "label": "Storage", "description": "Persistence and record browsing controls."},
    "analytics": {"domain": "analytics", "label": "Analytics", "description": "Dashboard and analytics access."},
    "brand": {"domain": "brand", "label": "Brands", "description": "Brand registry and brand metadata access."},
    "user": {"domain": "user", "label": "Users", "description": "User and role management controls."},
    "system": {"domain": "system", "label": "System", "description": "System configuration access."},
    "admin": {"domain": "admin", "label": "Admin", "description": "Full administrative access."},
}


def normalize_permission_name(value: str) -> str:
    return str(value or "").strip().lower()


def is_valid_permission(value: str) -> bool:
    return normalize_permission_name(value) in PERMISSION_REGISTRY


def get_permission(value: str) -> dict[str, Any]:
    permission = PERMISSION_REGISTRY.get(normalize_permission_name(value))
    return dict(permission or {})


def list_permissions() -> list[dict[str, Any]]:
    return [dict(permission) for permission in PERMISSION_REGISTRY.values()]


def permissions_by_domain() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for permission in list_permissions():
        grouped.setdefault(str(permission.get("domain", "general")), []).append(permission)
    return grouped


def list_permission_domains() -> list[dict[str, Any]]:
    grouped_permissions = permissions_by_domain()
    domains: list[dict[str, Any]] = []
    for domain_key, domain_meta in PERMISSION_DOMAINS.items():
        domains.append(
            {
                **dict(domain_meta),
                "permission_count": len(grouped_permissions.get(domain_key, [])),
                "permissions": [dict(permission) for permission in grouped_permissions.get(domain_key, [])],
            }
        )
    return domains
