"""Organization health helpers."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_dict, safe_int, safe_list, safe_text


def build_organization_health(
    organization: dict[str, Any] | None,
    teams: list[dict[str, Any]] | None = None,
    members: list[dict[str, Any]] | None = None,
    brands: list[dict[str, Any]] | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    organization = safe_dict(organization)
    teams = [safe_dict(item) for item in safe_list(teams)]
    members = [safe_dict(item) for item in safe_list(members)]
    brands = [safe_dict(item) for item in safe_list(brands)]
    settings = safe_dict(settings or organization.get("settings"))
    warnings: list[str] = []
    score = 100

    active_members = [item for item in members if safe_text(item.get("status", "active"), limit=40).lower() == "active"]
    active_teams = [item for item in teams if safe_text(item.get("status", "active"), limit=40).lower() == "active"]
    active_brands = [item for item in brands if safe_text(item.get("access_level", "use"), limit=40)]

    if not organization.get("owner_user_id"):
        score -= 20
        warnings.append("Organization owner is missing.")
    elif not any(str(item.get("user_id", "")) == str(organization.get("owner_user_id", "")) and safe_text(item.get("status", "active"), limit=40).lower() == "active" for item in members):
        score -= 15
        warnings.append("Organization owner membership is missing or inactive.")

    if not active_members:
        score -= 20
        warnings.append("No active members found.")
    if not active_teams:
        score -= 15
        warnings.append("No active teams found.")
    if not active_brands:
        score -= 10
        warnings.append("No active brand access found.")

    required_settings = ["default_brand", "default_platform", "default_language", "timezone", "features", "limits"]
    missing_settings = [key for key in required_settings if key not in settings or settings.get(key) in (None, "", {}, [])]
    if missing_settings:
        score -= min(20, 5 * len(missing_settings))
        warnings.append(f"Organization settings are missing: {', '.join(missing_settings)}.")

    if not isinstance(settings.get("limits", {}), dict):
        score -= 10
        warnings.append("Organization limits are incomplete.")

    score = max(0, min(100, score))
    if score >= 80:
        status = "healthy"
    elif score >= 50:
        status = "warning"
    else:
        status = "critical"

    return {
        "health_score": score,
        "health_status": status,
        "warnings": warnings,
        "metadata": {
            "active_members": len(active_members),
            "active_teams": len(active_teams),
            "active_brands": len(active_brands),
            "configuration_complete": not bool(missing_settings),
            "settings_valid": isinstance(settings.get("limits", {}), dict),
        },
    }
