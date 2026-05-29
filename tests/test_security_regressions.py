from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app


def _admin_client(auth_services) -> tuple[TestClient, str]:
    app = create_app(services={**auth_services})
    client = TestClient(app)
    register = client.post("/auth/register", json={"email": "admin-regression@example.com", "password": "Password123", "display_name": "Admin"})
    token = register.json()["data"]["access_token"]
    return client, token


def test_security_regressions_cover_route_and_role_rules(auth_services) -> None:
    client, admin_token = _admin_client(auth_services)
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    viewer_register = client.post("/auth/register", json={"email": "viewer-regression@example.com", "password": "Password123", "display_name": "Viewer"})
    viewer_token = viewer_register.json()["data"]["access_token"]
    viewer_id = viewer_register.json()["data"]["user"]["user_id"]

    assert client.post("/generate", json={"brand": "wenzel_partner", "platform": "instagram", "content_type": "property_description", "objective": "generate_leads", "audience": "relocation_clients", "location": "mallorca"}).status_code == 401
    assert client.post("/generate", json={"brand": "wenzel_partner", "platform": "instagram", "content_type": "property_description", "objective": "generate_leads", "audience": "relocation_clients", "location": "mallorca"}, headers={"Authorization": f"Bearer {viewer_token}"}).status_code == 403
    assert client.patch(f"/users/{viewer_id}/role", json={"role": "admin"}, headers={"Authorization": f"Bearer {viewer_token}"}).status_code == 403

    editor_assign = client.patch(f"/users/{viewer_id}/role", json={"role": "editor"}, headers=admin_headers)
    assert editor_assign.status_code == 200

    manager_register = client.post("/auth/register", json={"email": "manager-regression@example.com", "password": "Password123", "display_name": "Manager"})
    manager_token = manager_register.json()["data"]["access_token"]
    manager_id = manager_register.json()["data"]["user"]["user_id"]
    manager_role = client.patch(f"/users/{manager_id}/role", json={"role": "manager"}, headers=admin_headers)
    assert manager_role.status_code == 200
    assert client.patch(f"/users/{manager_id}/role", json={"role": "admin"}, headers={"Authorization": f"Bearer {manager_token}"}).status_code == 403

    disabled_assign = client.patch(f"/users/{viewer_id}/role", json={"role": "disabled"}, headers=admin_headers)
    assert disabled_assign.status_code == 200
    assert client.post("/generate", json={"brand": "wenzel_partner", "platform": "instagram", "content_type": "property_description", "objective": "generate_leads", "audience": "relocation_clients", "location": "mallorca"}, headers={"Authorization": f"Bearer {viewer_token}"}).status_code in {401, 403}


def test_security_rate_limit_returns_safe_429(auth_services, monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_RATE_LIMIT_TEST_MODE", "true")
    app = create_app(services={**auth_services})
    client = TestClient(app)
    register = client.post("/auth/register", json={"email": "rl@example.com", "password": "Password123", "display_name": "Rate Limit"})
    token = register.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setenv("ENABLE_RATE_LIMIT_TEST_MODE", "false")
    monkeypatch.setenv("ADMIN_RATE_LIMIT_PER_HOUR", "1")
    first = client.get("/security/status", headers=headers)
    second = client.get("/security/status", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["success"] is False
