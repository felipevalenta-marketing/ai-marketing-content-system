from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.auth.auth_manager import AuthManager, AuthService
from src.api.main import create_app
from src.users.user_manager import UserManager


def test_api_auth_register_login_and_me(auth_services) -> None:
    app = create_app(services={**auth_services})
    client = TestClient(app)

    register = client.post("/auth/register", json={"email": "auth@example.com", "password": "Password123", "display_name": "Auth User"})
    assert register.status_code == 200
    assert register.json()["success"] is True
    token = register.json()["data"]["access_token"]
    assert token
    assert "password_hash" not in register.json()["data"]["user"]

    login = client.post("/auth/login", json={"email": "auth@example.com", "password": "Password123"})
    assert login.status_code == 200
    assert login.json()["success"] is True

    invalid_login = client.post("/auth/login", json={"email": "auth@example.com", "password": "WrongPassword123"})
    assert invalid_login.status_code == 401
    assert invalid_login.json()["success"] is False
    assert any("invalid credentials" in error.lower() for error in invalid_login.json()["errors"])

    missing = client.get("/auth/me")
    assert missing.status_code == 401
    assert missing.json()["success"] is False

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["success"] is True
    assert me.json()["data"]["email"] == "auth@example.com"
    assert "access_token" not in me.json()["data"]

    logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 200
    assert logout.json()["success"] is True


def test_api_auth_login_returns_500_when_jwt_secret_missing_in_production(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    users = UserManager(storage_path=str(tmp_path / "users"))
    auth = AuthService(AuthManager(user_manager=users, jwt_secret="", jwt_expiration_hours=24))
    app = create_app(services={"users": users, "auth": auth})
    client = TestClient(app)

    register = client.post("/auth/register", json={"email": "prod@example.com", "password": "Password123", "display_name": "Prod User"})
    assert register.status_code == 200
    assert register.json()["success"] is True
    assert register.json()["data"]["access_token"] == ""

    login = client.post("/auth/login", json={"email": "prod@example.com", "password": "Password123"})
    assert login.status_code == 500
    payload = login.json()
    assert payload["success"] is False
    assert any("authentication service is unavailable" in error.lower() for error in payload["errors"])
