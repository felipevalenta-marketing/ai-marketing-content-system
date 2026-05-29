"""Authentication validation helpers."""

from __future__ import annotations

from typing import Any

from src.auth.jwt_manager import verify_access_token
from src.auth.password_manager import validate_password_strength
from src.users.user_validator import validate_email


def validate_registration_request(email: str, password: str, duplicate_user: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    email_validation = validate_email(email)
    password_validation = validate_password_strength(password)
    if not email_validation["valid"]:
        errors.extend(email_validation["errors"])
    if duplicate_user:
        errors.append("Email already exists.")
    if not password_validation["valid"]:
        errors.extend(password_validation["errors"])
    warnings.extend(password_validation["warnings"])
    return {"valid": not errors, "warnings": warnings, "errors": errors}


def validate_login_request(email: str, password: str) -> dict[str, Any]:
    email_validation = validate_email(email)
    errors = list(email_validation["errors"])
    if not str(password or "").strip():
        errors.append("Password is required.")
    return {"valid": not errors, "warnings": [], "errors": errors}


def validate_jwt(token: str, secret: str | None = None) -> dict[str, Any]:
    verification = verify_access_token(token, secret=secret)
    return {"valid": bool(verification.get("valid")), "warnings": list(verification.get("warnings", [])), "errors": list(verification.get("errors", [])), "payload": verification.get("payload", {})}
