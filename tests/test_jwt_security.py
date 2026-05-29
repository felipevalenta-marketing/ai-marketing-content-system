from __future__ import annotations

from src.auth.jwt_manager import create_access_token
from src.security.jwt_security import validate_jwt_security


def test_jwt_security_accepts_valid_token() -> None:
    secret = "x" * 32
    token = create_access_token({"sub": "user-1", "iss": "amcs"}, expires_in_hours=1, secret=secret)
    result = validate_jwt_security(token, secret=secret, issuer="amcs")
    assert result["valid"] is True
    assert result["errors"] == []


def test_jwt_security_rejects_expired_token() -> None:
    secret = "x" * 32
    token = create_access_token({"sub": "user-1"}, expires_in_hours=-1, secret=secret)
    result = validate_jwt_security(token, secret=secret)
    assert result["valid"] is False
    assert any("expired" in error.lower() for error in result["errors"])


def test_jwt_security_rejects_malformed_token() -> None:
    result = validate_jwt_security("not-a-token", secret="x" * 32)
    assert result["valid"] is False
    assert any("malformed" in error.lower() for error in result["errors"])

