from __future__ import annotations

import pytest

from src.auth.jwt_manager import create_access_token, decode_access_token, verify_access_token


def test_jwt_create_decode_and_verify() -> None:
    token = create_access_token({"sub": "usr_1", "email": "user@example.com"}, expires_in_hours=24, secret="test-secret")
    assert token
    decoded = decode_access_token(token, secret="test-secret")
    assert decoded["sub"] == "usr_1"
    verification = verify_access_token(token, secret="test-secret")
    assert verification["valid"] is True


def test_jwt_expired_token_is_invalid() -> None:
    token = create_access_token({"sub": "usr_1", "email": "user@example.com"}, expires_in_hours=-1, secret="test-secret")
    verification = verify_access_token(token, secret="test-secret")
    assert verification["valid"] is False
    assert any("expired" in error.lower() for error in verification["errors"])


def test_jwt_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    token = create_access_token({"sub": "usr_1", "email": "user@example.com"}, expires_in_hours=24)

    assert token
    decoded = decode_access_token(token)
    assert decoded["sub"] == "usr_1"
    assert decoded["email"] == "user@example.com"


def test_token_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("APP_ENV", "development")

    token = create_access_token({"sub": "usr_1", "email": "user@example.com"}, expires_in_hours=24)
    valid = verify_access_token(token)
    assert valid["valid"] is True

    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    invalid = verify_access_token(tampered)
    assert invalid["valid"] is False
