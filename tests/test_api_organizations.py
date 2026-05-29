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


def test_api_organizations_endpoints_and_rbac(auth_services, tmp_path) -> None:
    app = create_app(services=_build_services(auth_services, tmp_path))
    client = TestClient(app)

    missing = client.get("/organizations")
    assert missing.status_code == 401

    admin_register = client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "Password123", "display_name": "Admin User"},
    )
    assert admin_register.status_code == 200
    admin_token = admin_register.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    viewer_register = client.post(
        "/auth/register",
        json={"email": "viewer@example.com", "password": "Password123", "display_name": "Viewer User"},
    )
    viewer_token = viewer_register.json()["data"]["access_token"]
    viewer_user_id = viewer_register.json()["data"]["user"]["user_id"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    created = client.post(
        "/organizations",
        headers=admin_headers,
        json={"name": "Acme Studio", "slug": "acme-studio"},
    )
    assert created.status_code == 200
    organization_id = created.json()["data"]["organization_id"]

    forbidden_create = client.post(
        "/organizations",
        headers=viewer_headers,
        json={"name": "Other Studio", "slug": "other-studio"},
    )
    assert forbidden_create.status_code == 403

    forbidden_read = client.get(f"/organizations/{organization_id}", headers=viewer_headers)
    assert forbidden_read.status_code == 200
    assert forbidden_read.json()["success"] is False
    assert forbidden_read.json()["errors"]

    organization = client.get(f"/organizations/{organization_id}", headers=admin_headers)
    assert organization.status_code == 200
    assert organization.json()["data"]["organization_id"] == organization_id

    profile = client.get(f"/organizations/{organization_id}/profile", headers=admin_headers)
    assert profile.status_code == 200
    assert profile.json()["data"]["tenant_ready"] is True

    health = client.get(f"/organizations/{organization_id}/health", headers=admin_headers)
    assert health.status_code == 200
    assert "health_score" in health.json()["data"]

    context = client.get(f"/organizations/{organization_id}/context", headers=admin_headers)
    assert context.status_code == 200
    assert context.json()["data"]["organization_id"] == organization_id
    assert context.json()["data"]["tenant_ready"] is True
    assert "role_bridge" in context.json()["data"]

    added = client.post(
        f"/organizations/{organization_id}/members",
        headers=admin_headers,
        json={"user_id": viewer_user_id, "role": "member"},
    )
    assert added.status_code == 200
    assert added.json()["data"]["user_id"] == viewer_user_id

    members = client.get(f"/organizations/{organization_id}/members", headers=admin_headers)
    assert members.status_code == 200
    assert members.json()["data"]["count"] >= 2

    granted = client.post(
        f"/organizations/{organization_id}/brands",
        headers=admin_headers,
        json={"brand_id": "wenzel_partner", "access_level": "manage"},
    )
    assert granted.status_code == 200

    brands = client.get(f"/organizations/{organization_id}/brands", headers=admin_headers)
    assert brands.status_code == 200
    assert brands.json()["data"]["count"] == 1


def test_api_organizations_rejects_invalid_brand_access(auth_services, tmp_path) -> None:
    app = create_app(services=_build_services(auth_services, tmp_path))
    client = TestClient(app)

    register = client.post(
        "/auth/register",
        json={"email": "admin2@example.com", "password": "Password123", "display_name": "Admin User"},
    )
    token = register.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post("/organizations", headers=headers, json={"name": "Acme Studio", "slug": "acme-studio"})
    organization_id = created.json()["data"]["organization_id"]

    invalid_brand = client.post(
        f"/organizations/{organization_id}/brands",
        headers=headers,
        json={"brand_id": "missing_brand", "access_level": "manage"},
    )
    assert invalid_brand.status_code == 200
    assert invalid_brand.json()["success"] is False
    assert invalid_brand.json()["errors"]
