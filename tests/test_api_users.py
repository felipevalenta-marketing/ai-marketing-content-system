from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app


def test_api_users_profile_get_and_patch(auth_services) -> None:
    app = create_app(services={**auth_services})
    client = TestClient(app)

    register = client.post("/auth/register", json={"email": "profile@example.com", "password": "Password123", "display_name": "Profile User"})
    token = register.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    profile = client.get("/users/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["success"] is True
    assert profile.json()["data"]["email"] == "profile@example.com"

    updated = client.patch("/users/profile", headers=headers, json={"display_name": "Updated Name", "settings": {"theme": "dark"}})
    assert updated.status_code == 200
    assert updated.json()["success"] is True
    assert updated.json()["data"]["display_name"] == "Updated Name"
    assert updated.json()["data"]["settings"]["theme"] == "dark"
