from __future__ import annotations

from pathlib import Path

import pytest

from src.auth.auth_manager import AuthManager, AuthService
from src.users.user_manager import UserManager


def test_auth_service_register_login_and_logout(tmp_path: Path) -> None:
    users = UserManager(storage_path=str(tmp_path / "users"))
    auth = AuthService(AuthManager(user_manager=users, jwt_secret="test-secret", jwt_expiration_hours=24))

    registered = auth.register("user@example.com", "Password123", "Test User")
    assert registered["success"] is True
    assert registered["access_token"]
    assert "password_hash" not in registered["user"]

    logged_in = auth.login("user@example.com", "Password123")
    assert logged_in["success"] is True
    assert logged_in["access_token"]

    authenticated = auth.authenticate(logged_in["access_token"])
    assert authenticated["success"] is True
    assert authenticated["user"]["email"] == "user@example.com"

    logged_out = auth.logout(logged_in["access_token"])
    assert logged_out["success"] is True


def test_login_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    users = UserManager(storage_path=str(tmp_path / "users"))
    auth = AuthService(AuthManager(user_manager=users, jwt_secret="", jwt_expiration_hours=24))

    registered = auth.register("user@example.com", "Password123", "Test User")
    assert registered["success"] is True
    assert registered["access_token"]

    logged_in = auth.login("user@example.com", "Password123")
    assert logged_in["success"] is True
    assert logged_in["access_token"]
    assert logged_in["token_type"] == "bearer"


def test_login_invalid_password(tmp_path: Path) -> None:
    users = UserManager(storage_path=str(tmp_path / "users"))
    auth = AuthService(AuthManager(user_manager=users, jwt_secret="test-secret", jwt_expiration_hours=24))

    auth.register("user@example.com", "Password123", "Test User")
    invalid = auth.login("user@example.com", "WrongPassword123")

    assert invalid["success"] is False
    assert any("invalid credentials" in error.lower() for error in invalid["errors"])


def test_auth_service_rejects_duplicate_users(tmp_path: Path) -> None:
    users = UserManager(storage_path=str(tmp_path / "users"))
    auth = AuthService(AuthManager(user_manager=users, jwt_secret="test-secret", jwt_expiration_hours=24))
    assert auth.register("user@example.com", "Password123", "Test User")["success"] is True
    duplicate = auth.register("user@example.com", "Password123", "Test User")
    assert duplicate["success"] is False
    assert any("exists" in error.lower() for error in duplicate["errors"])


def test_auth_service_rejects_invalid_credentials(tmp_path: Path) -> None:
    users = UserManager(storage_path=str(tmp_path / "users"))
    auth = AuthService(AuthManager(user_manager=users, jwt_secret="test-secret", jwt_expiration_hours=24))
    auth.register("user@example.com", "Password123", "Test User")
    invalid = auth.login("user@example.com", "WrongPassword123")
    assert invalid["success"] is False
    assert any("invalid credentials" in error.lower() for error in invalid["errors"])


def test_auth_service_register_persists_user_without_jwt_secret(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    users = UserManager(storage_path=str(tmp_path / "users"))
    auth = AuthService(AuthManager(user_manager=users, jwt_secret="", jwt_expiration_hours=24))

    registered = auth.register("persist@example.com", "Password123", "Persist User")

    assert registered["success"] is True
    assert registered["access_token"] == ""
    stored = users.get_user_record_by_email("persist@example.com")
    assert stored is not None
    assert stored["email"] == "persist@example.com"
