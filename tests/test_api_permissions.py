from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app


def test_api_permission_protected_routes(auth_services) -> None:
    app = create_app(services={**auth_services})
    client = TestClient(app)

    admin_register = client.post("/auth/register", json={"email": "admin2@example.com", "password": "Password123", "display_name": "Admin"})
    admin_token = admin_register.json()["data"]["access_token"]

    viewer_register = client.post("/auth/register", json={"email": "viewer2@example.com", "password": "Password123", "display_name": "Viewer"})
    viewer_token = viewer_register.json()["data"]["access_token"]
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    unauth_generate = client.post("/generate", json={"brand": "wenzel_partner", "platform": "instagram", "content_type": "instagram_post", "objective": "generate_leads", "audience": "relocation_clients", "location": "sant_llorenc_des_cardassar"})
    assert unauth_generate.status_code == 401

    viewer_generate = client.post("/generate", json={"brand": "wenzel_partner", "platform": "instagram", "content_type": "instagram_post", "objective": "generate_leads", "audience": "relocation_clients", "location": "sant_llorenc_des_cardassar"}, headers=viewer_headers)
    assert viewer_generate.status_code == 403

    analytics = client.get("/analytics/dashboard", headers=viewer_headers)
    assert analytics.status_code == 200

    config_denied = client.get("/config", headers=viewer_headers)
    assert config_denied.status_code == 403

    config_allowed = client.get("/config", headers={"Authorization": f"Bearer {admin_token}"})
    assert config_allowed.status_code == 200

    admin_role = client.patch(f"/users/{viewer_register.json()['data']['user']['user_id']}/role", json={"role": "editor"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_role.status_code == 200

    editor_generate = client.post("/generate", json={"brand": "wenzel_partner", "platform": "instagram", "content_type": "instagram_post", "objective": "generate_leads", "audience": "relocation_clients", "location": "sant_llorenc_des_cardassar", "dry_run": True}, headers=viewer_headers)
    assert editor_generate.status_code == 200
