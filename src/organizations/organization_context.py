"""Organization context helpers."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_dict, safe_text

MEMBERSHIP_ROLE_BRIDGE = {
    "owner": "admin",
    "admin": "admin",
    "manager": "manager",
    "member": "editor",
    "viewer": "viewer",
}


def get_membership_role_bridge() -> dict[str, str]:
    return dict(MEMBERSHIP_ROLE_BRIDGE)


def build_context(
    organization_manager: Any,
    *,
    user: dict[str, Any] | None = None,
    organization_id: str | None = None,
    team_id: str | None = None,
    brand_id: str | None = None,
) -> dict[str, Any]:
    user = safe_dict(user)
    organization_id = safe_text(organization_id or user.get("active_organization_id"), limit=120)
    team_id = safe_text(team_id or user.get("active_team_id"), limit=120)
    brand_id = safe_text(brand_id or user.get("active_brand_id") or user.get("brand_id"), limit=120)
    organization_profile = organization_manager.build_organization_profile(organization_id) if organization_id else {}
    teams = safe_dict(organization_profile).get("teams", [])
    members = safe_dict(organization_profile).get("members", [])
    brands = safe_dict(organization_profile).get("brands", [])
    active_team = next((item for item in teams if str(item.get("team_id", "")) == team_id), None) if isinstance(teams, list) else None
    active_brand = next((item for item in brands if str(item.get("brand_id", "")) == brand_id), None) if isinstance(brands, list) else None
    return {
        "organization_id": organization_id,
        "team_id": team_id,
        "brand_id": brand_id,
        "organization": organization_profile.get("organization", organization_profile),
        "organization_profile": organization_profile,
        "active_team": active_team or {},
        "active_brand": active_brand or {},
        "teams": teams,
        "members": members,
        "brands": brands,
        "tenant_ready": True,
        "role_bridge": get_membership_role_bridge(),
        "metadata": {
            "created_by": safe_text(user.get("user_id", ""), limit=120),
            "updated_by": safe_text(user.get("user_id", ""), limit=120),
        },
    }


def validate_context(context: dict[str, Any] | None) -> dict[str, Any]:
    payload = safe_dict(context)
    warnings: list[str] = []
    errors: list[str] = []
    if not payload.get("organization_id"):
        errors.append("organization_id is required.")
    if not payload.get("organization"):
        errors.append("Organization context is missing.")
    if payload.get("team_id") and not payload.get("active_team"):
        warnings.append("Selected team is not present in organization context.")
    if payload.get("brand_id") and not payload.get("active_brand"):
        warnings.append("Selected brand is not present in organization context.")
    return {"valid": not errors, "warnings": warnings, "errors": errors}


def get_active_context(organization_manager: Any, user: dict[str, Any] | None = None) -> dict[str, Any]:
    return build_context(organization_manager, user=user)
