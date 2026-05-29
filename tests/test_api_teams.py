from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.organizations.organization_manager import OrganizationManager
from src.rbac.rbac_manager import RBACManager


def _build_services(auth_services: dict[str, object], tmp_path) -> dict[str, object]:
    users = auth_services["users"]
    organization_manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)
    return {
        **auth_services,
        "rbac": RBACManager(users),
        "organizations": organization_manager,
        "teams": organization_manager.membership_manager.team_manager,
        "memberships": organization_manager.membership_manager,
        "brand_access": organization_manager.brand_access_manager,
    }


def test_api_teams_endpoints_and_org_access(auth_services, tmp_path) -> None:
    app = create_app(services=_build_services(auth_services, tmp_path))
    client = TestClient(app)

    admin_register = client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "Password123", "display_name": "Admin User"},
    )
    admin_token = admin_register.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    viewer_register = client.post(
        "/auth/register",
        json={"email": "viewer@example.com", "password": "Password123", "display_name": "Viewer User"},
    )
    viewer_token = viewer_register.json()["data"]["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    created_org = client.post("/organizations", headers=admin_headers, json={"name": "Acme Studio", "slug": "acme-studio"})
    organization_id = created_org.json()["data"]["organization_id"]

    forbidden = client.post(
        f"/organizations/{organization_id}/teams",
        headers=viewer_headers,
        json={"name": "Creative Team", "slug": "creative-team"},
    )
    assert forbidden.status_code == 403

    created_team = client.post(
        f"/organizations/{organization_id}/teams",
        headers=admin_headers,
        json={"name": "Creative Team", "slug": "creative-team"},
    )
    assert created_team.status_code == 200
    team_id = created_team.json()["data"]["team_id"]

    listed = client.get(f"/organizations/{organization_id}/teams", headers=admin_headers)
    assert listed.status_code == 200
    assert listed.json()["data"]["count"] == 1

    get_team = client.get(f"/teams/{team_id}", headers=admin_headers)
    assert get_team.status_code == 200
    assert get_team.json()["data"]["team_id"] == team_id

    viewer_list = client.get(f"/organizations/{organization_id}/teams", headers=viewer_headers)
    assert viewer_list.status_code == 200
    assert viewer_list.json()["success"] is False
    assert viewer_list.json()["errors"]
