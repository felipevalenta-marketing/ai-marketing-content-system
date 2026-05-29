from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app


def test_api_auth_register_login_and_me(auth_services) -> None:
    app = create_app(services={**auth_services})
    client = TestClient(app)

    register = client.post("/auth/register", json={"email": "auth@example.com", "password": "Password123", "display_name": "Auth User"})
    assert register.status_code == 200
    assert register.json()["success"] is True
    token = register.json()["data"]["access_token"]
    assert token

    login = client.post("/auth/login", json={"email": "auth@example.com", "password": "Password123"})
    assert login.status_code == 200
    assert login.json()["success"] is True

    missing = client.get("/auth/me")
    assert missing.status_code == 401
    assert missing.json()["success"] is False

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["success"] is True
    assert me.json()["data"]["email"] == "auth@example.com"

    logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 200
    assert logout.json()["success"] is True
