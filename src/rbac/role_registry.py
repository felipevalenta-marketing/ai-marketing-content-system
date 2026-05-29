"""Default role registry."""

from __future__ import annotations

from typing import Any


ROLE_REGISTRY: dict[str, dict[str, Any]] = {
    "admin": {
        "role": "admin",
        "label": "Admin",
        "description": "Full platform access.",
        "type": "system",
        "inherits_from": ["manager"],
        "permissions": ["admin:all"],
        "level": 100,
    },
    "manager": {
        "role": "manager",
        "label": "Manager",
        "description": "Can run workflows, manage reports, and view analytics.",
        "type": "system",
        "inherits_from": ["editor"],
        "permissions": [
            "generation:read",
            "generation:create",
            "workflow:read",
            "workflow:run",
            "campaign:read",
            "campaign:create",
            "asset:read",
            "asset:create",
            "report:read",
            "report:create",
            "report:export",
            "storage:read",
            "analytics:read",
            "brand:read",
            "system:read",
        ],
        "level": 80,
    },
    "editor": {
        "role": "editor",
        "label": "Editor",
        "description": "Can generate content and run basic workflows.",
        "type": "system",
        "inherits_from": ["viewer"],
        "permissions": [
            "generation:read",
            "generation:create",
            "workflow:read",
            "workflow:run",
            "campaign:read",
            "campaign:create",
            "asset:read",
            "asset:create",
            "report:read",
            "report:create",
            "analytics:read",
            "brand:read",
        ],
        "level": 60,
    },
    "viewer": {
        "role": "viewer",
        "label": "Viewer",
        "description": "Can view dashboards, reports, analytics, and storage summaries.",
        "type": "system",
        "inherits_from": [],
        "permissions": [
            "generation:read",
            "workflow:read",
            "campaign:read",
            "asset:read",
            "report:read",
            "storage:read",
            "analytics:read",
            "brand:read",
        ],
        "level": 20,
    },
    "disabled": {
        "role": "disabled",
        "label": "Disabled",
        "description": "No platform access except logout/profile.",
        "type": "system",
        "inherits_from": [],
        "permissions": [],
        "level": 0,
    },
}


def normalize_role_name(value: str) -> str:
    return str(value or "").strip().lower()


def is_valid_role(value: str) -> bool:
    return normalize_role_name(value) in ROLE_REGISTRY


def get_role(value: str) -> dict[str, Any]:
    role = ROLE_REGISTRY.get(normalize_role_name(value))
    return dict(role or {})


def list_roles() -> list[dict[str, Any]]:
    return [dict(role) for role in ROLE_REGISTRY.values()]


def get_role_level(value: str) -> int:
    role = get_role(value)
    return int(role.get("level", 0) or 0)


def role_has_at_least(value: str, minimum_role: str) -> bool:
    return get_role_level(value) >= get_role_level(minimum_role)


def get_role_hierarchy() -> list[dict[str, Any]]:
    return sorted(list_roles(), key=lambda item: int(item.get("level", 0) or 0), reverse=True)
