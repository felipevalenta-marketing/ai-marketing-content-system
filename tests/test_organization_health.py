from __future__ import annotations

from src.organizations.organization_health import build_organization_health


def test_organization_health_scores_and_status() -> None:
    organization = {"owner_user_id": "user_1", "settings": {"default_brand": "wenzel_partner", "default_platform": "instagram", "default_language": "en", "timezone": "Europe/Madrid", "features": {}, "limits": {}}}
    teams = [{"status": "active"}]
    members = [{"user_id": "user_1", "status": "active"}]
    brands = [{"brand_id": "wenzel_partner", "access_level": "manage"}]

    health = build_organization_health(organization, teams, members, brands, organization["settings"])

    assert 0 <= health["health_score"] <= 100
    assert health["health_status"] in {"healthy", "warning", "critical"}
    assert isinstance(health["warnings"], list)
    assert health["metadata"]["active_members"] == 1
    assert health["metadata"]["active_teams"] == 1
    assert health["metadata"]["active_brands"] == 1

