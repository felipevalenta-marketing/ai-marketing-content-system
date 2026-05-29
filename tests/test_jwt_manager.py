from __future__ import annotations

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
