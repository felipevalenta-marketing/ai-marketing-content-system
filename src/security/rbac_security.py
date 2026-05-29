"""RBAC hardening helpers."""

from __future__ import annotations

from typing import Any

from src.rbac.rbac_manager import RBACManager
from src.users.user_manager import UserManager


def build_rbac_security_summary(
    *,
    actor: dict[str, Any] | None = None,
    target: dict[str, Any] | None = None,
    organization_id: str = "",
    team_id: str = "",
    target_organization_id: str = "",
    target_team_id: str = "",
) -> dict[str, Any]:
    actor = dict(actor or {})
    target = dict(target or {})
    actor_role = str(actor.get("role", "disabled")).lower()
    target_role = str(target.get("role", "viewer")).lower()
    user_manager = UserManager()
    rbac = RBACManager(user_manager)
    escalation_blocked = False
    warnings: list[str] = []
    errors: list[str] = []
    if actor_role == "disabled":
        errors.append("Disabled users cannot perform RBAC actions.")
        escalation_blocked = True
    if target_role and not rbac.has_any_permission(actor, ["user:manage", "admin:all"]):
        errors.append("Insufficient permission to manage roles.")
        escalation_blocked = True
    if organization_id and target_organization_id and str(organization_id) != str(target_organization_id):
        errors.append("Organization boundary protection blocked the action.")
        escalation_blocked = True
    if team_id and target_team_id and str(team_id) != str(target_team_id):
        errors.append("Team boundary protection blocked the action.")
        escalation_blocked = True
    if actor.get("user_id") and target.get("user_id") and actor.get("user_id") == target.get("user_id") and actor_role != "admin":
        errors.append("Self-escalation is blocked.")
        escalation_blocked = True
    return {
        "allowed": not escalation_blocked,
        "actor_role": actor_role,
        "target_role": target_role,
        "organization_boundary_protected": bool(organization_id or target_organization_id),
        "team_boundary_protected": bool(team_id or target_team_id),
        "warnings": warnings,
        "errors": errors,
        "backend_authoritative": True,
    }

