from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app


def test_api_rbac_endpoints_and_role_assignment(auth_services) -> None:
    app = create_app(services={**auth_services})
    client = TestClient(app)

    admin_register = client.post("/auth/register", json={"email": "admin@example.com", "password": "Password123", "display_name": "Admin"})
    admin_token = admin_register.json()["data"]["access_token"]
    admin_user_id = admin_register.json()["data"]["user"]["user_id"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    roles = client.get("/rbac/roles", headers=headers)
    permissions = client.get("/rbac/permissions", headers=headers)
    health = client.get("/rbac/health", headers=headers)
    access = client.get("/rbac/me", headers=headers)
    users = client.get("/users", headers=headers)

    assert roles.status_code == 200
    assert permissions.status_code == 200
    assert health.status_code == 200
    assert access.status_code == 200
    assert users.status_code == 200
    assert access.json()["data"]["role"] == "admin"
    assert access.json()["data"]["role_type"] == "system"
    assert "permission_domains" in access.json()["data"]

    viewer_register = client.post("/auth/register", json={"email": "viewer@example.com", "password": "Password123", "display_name": "Viewer"})
    viewer_user_id = viewer_register.json()["data"]["user"]["user_id"]
    denied = client.patch(f"/users/{viewer_user_id}/role", json={"role": "admin"}, headers={"Authorization": f"Bearer {viewer_register.json()['data']['access_token']}"})
    assert denied.status_code == 403

    assigned = client.patch(f"/users/{viewer_user_id}/role", json={"role": "editor"}, headers=headers)
    assert assigned.status_code == 200
    assert assigned.json()["success"] is True
