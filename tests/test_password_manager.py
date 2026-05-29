from __future__ import annotations

from src.auth.password_manager import hash_password, validate_password_strength, verify_password


def test_password_hash_and_verify() -> None:
    hashed = hash_password("Password123")
    assert hashed
    assert verify_password("Password123", hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_password_strength_warnings() -> None:
    weak = validate_password_strength("short")
    assert weak["valid"] is False
    assert weak["errors"]
    assert weak["warnings"]
