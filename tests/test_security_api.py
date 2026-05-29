from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.api_config import ApiConfig
from src.api.main import create_app


def _make_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
    monkeypatch.setenv("USER_STORAGE_PATH", str(tmp_path / "users"))
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "data"))
    monkeypatch.setenv("ENABLE_SECURITY_HARDENING", "true")
    monkeypatch.setenv("ENABLE_SECURITY_HEADERS", "true")
    monkeypatch.setenv("ENABLE_RATE_LIMITING", "true")
    app = create_app(ApiConfig())
    return TestClient(app)


def _login_admin(client: TestClient) -> str:
    register = client.post(
        "/auth/register",
        json={"email": "admin@example.com", "password": "Secret123!", "display_name": "Admin"},
    )
    assert register.status_code == 200
    token = register.json()["data"]["access_token"]
    assert token
    return token


def test_security_endpoints_require_authentication(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    response = client.get("/security/status")
    assert response.status_code == 401


def test_security_endpoints_allow_admin_access(tmp_path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    token = _login_admin(client)
    headers = {"Authorization": f"Bearer {token}"}
    status = client.get("/security/status", headers=headers)
    health = client.get("/security/health", headers=headers)
    baseline = client.get("/security/baseline", headers=headers)
    findings = client.get("/security/findings", headers=headers)
    dependencies = client.get("/security/dependencies", headers=headers)
    policy = client.get("/security/policy", headers=headers)
    configuration = client.get("/security/configuration", headers=headers)
    assert status.status_code == 200
    assert health.status_code == 200
    assert baseline.status_code == 200
    assert findings.status_code == 200
    assert dependencies.status_code == 200
    assert policy.status_code == 200
    assert configuration.status_code == 200
    assert status.json()["success"] is True
    assert "security_score" in health.json()["data"]
    assert "baseline_ready" in baseline.json()["data"]
    assert "findings" in findings.json()["data"]
    assert "dependencies_valid" in dependencies.json()["data"]
    assert "active_protections" in configuration.json()["data"]
    assert "required_checks" in policy.json()["data"]
