from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.configuration.config_manager import ConfigManager


def test_api_configuration_endpoints_and_feature_updates(auth_services, tmp_path) -> None:
    configuration = ConfigManager(config_root=str(tmp_path / "config"))
    app = create_app(services={"configuration": configuration, **auth_services})
    client = TestClient(app)

    register = client.post("/auth/register", json={"email": "config@example.com", "password": "Password123", "display_name": "Config User"})
    token = register.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    summary = client.get("/configuration", headers=headers)
    platform = client.get("/configuration/platform", headers=headers)
    features = client.get("/configuration/features", headers=headers)
    modules = client.get("/configuration/modules", headers=headers)
    limits = client.get("/configuration/limits", headers=headers)
    environment = client.get("/configuration/environment", headers=headers)
    health = client.get("/configuration/health", headers=headers)

    assert summary.status_code == 200
    assert platform.status_code == 200
    assert features.status_code == 200
    assert modules.status_code == 200
    assert limits.status_code == 200
    assert environment.status_code == 200
    assert health.status_code == 200
    assert summary.json()["data"]["configuration_health"]["valid"] is True
    assert "platform_config" in summary.json()["data"]
    assert client.get("/configuration").status_code == 401

    manager_register = client.post("/auth/register", json={"email": "manager@example.com", "password": "Password123", "display_name": "Manager"})
    manager_user_id = manager_register.json()["data"]["user"]["user_id"]
    admin_token = token
    admin_role = client.patch(f"/users/{manager_user_id}/role", json={"role": "manager"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_role.status_code == 200

    manager_headers = {"Authorization": f"Bearer {manager_register.json()['data']['access_token']}"}
    update = client.patch("/configuration/features/markdown_reports", json={"enabled": False}, headers=manager_headers)
    assert update.status_code == 200
    assert update.json()["data"]["value"] is False
    assert update.json()["data"]["configuration"]["configuration_health"]["valid"] is True

    allowed = client.patch("/configuration/features/analytics_dashboard", json={"enabled": True}, headers={"Authorization": f"Bearer {token}"})
    assert allowed.status_code == 200


def test_api_configuration_rejects_unknown_flags_and_forbidden_updates(auth_services, tmp_path) -> None:
    configuration = ConfigManager(config_root=str(tmp_path / "config"))
    app = create_app(services={"configuration": configuration, **auth_services})
    client = TestClient(app)

    admin_register = client.post("/auth/register", json={"email": "admin@example.com", "password": "Password123", "display_name": "Admin"})
    admin_token = admin_register.json()["data"]["access_token"]

    viewer_register = client.post("/auth/register", json={"email": "viewer@example.com", "password": "Password123", "display_name": "Viewer"})
    viewer_headers = {"Authorization": f"Bearer {viewer_register.json()['data']['access_token']}"}
    forbidden = client.patch("/configuration/features/markdown_reports", json={"enabled": False}, headers=viewer_headers)
    assert forbidden.status_code == 403

    rejected = client.patch("/configuration/features/unknown_flag", json={"enabled": True}, headers={"Authorization": f"Bearer {admin_token}"})
    assert rejected.status_code == 400
    assert rejected.json()["success"] is False
