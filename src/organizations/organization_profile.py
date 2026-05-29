"""Organization profile aggregation helpers."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_dict, safe_int, safe_list, safe_text

from .organization_health import build_organization_health
from .organization_context import get_membership_role_bridge


def build_organization_profile_payload(
    organization_manager: Any,
    organization_id: str,
    *,
    analytics_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    organization_getter = getattr(organization_manager, "get_organization", None)
    organization = safe_dict(organization_getter(organization_id) if callable(organization_getter) else {})
    if not organization:
        return {}
    team_manager = getattr(organization_manager, "team_manager", None) or getattr(getattr(organization_manager, "membership_manager", None), "team_manager", None)
    membership_manager = getattr(organization_manager, "membership_manager", None)
    brand_access_manager = getattr(organization_manager, "brand_access_manager", None)
    teams = safe_list(team_manager.list_teams(organization_id).get("data", {}).get("teams", [])) if team_manager else []
    members = safe_list(membership_manager.list_members(organization_id).get("data", {}).get("memberships", [])) if membership_manager else []
    brands = safe_list(brand_access_manager.list_organization_brands(organization_id).get("data", {}).get("brand_access", [])) if brand_access_manager else []
    settings = safe_dict(organization.get("settings"))
    health = build_organization_health(organization, teams, members, brands, settings)
    analytics = safe_dict(analytics_metadata)
    profile = {
        "organization": organization,
        "teams": [safe_dict(item) for item in teams],
        "members": [safe_dict(item) for item in members],
        "brands": [safe_dict(item) for item in brands],
        "settings": settings,
        "health": health,
        "tenant_ready": True,
        "tenant_configuration": {
            "tenant_ready": True,
            "tenant_limits": safe_dict(settings.get("limits")),
        },
        "tenant_limits": safe_dict(settings.get("limits")),
        "analytics": {
            "member_count": len(members),
            "team_count": len(teams),
            "brand_count": len(brands),
            "workflow_count": safe_int(analytics.get("workflow_count"), 0),
            "report_count": safe_int(analytics.get("report_count"), 0),
            "token_usage": safe_dict(analytics.get("token_usage")),
            "estimated_cost": safe_dict(analytics.get("estimated_cost")),
        },
        "role_bridge": get_membership_role_bridge(),
        "metadata": {
            **safe_dict(organization.get("metadata")),
            "tenant_ready": True,
            "organization_limits": safe_dict(settings.get("limits")),
            "created_at": organization.get("created_at", ""),
            "modified_at": organization.get("updated_at", ""),
            "file_count": len([item for item in teams if item]) + len([item for item in members if item]) + len([item for item in brands if item]),
            "markdown_count": 0,
            "configuration_present": bool(settings),
        },
    }
    profile.update(
        {
            "organization_id": organization.get("organization_id", ""),
            "name": organization.get("name", ""),
            "slug": organization.get("slug", ""),
            "status": organization.get("status", "active"),
            "created_at": organization.get("created_at", ""),
            "updated_at": organization.get("updated_at", ""),
            "owner_user_id": organization.get("owner_user_id", ""),
            "team_count": len(teams),
            "member_count": len(members),
            "brand_count": len(brands),
            "active_brand_ids": [str(item.get("brand_id", "")) for item in brands if item.get("brand_id")],
            "health_score": safe_int(health.get("health_score"), 0),
            "health_status": safe_text(health.get("health_status"), limit=40),
            "warnings": list(health.get("warnings", [])),
        }
    )
    return profile
