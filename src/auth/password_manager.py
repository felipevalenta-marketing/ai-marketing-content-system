"""Password hashing and validation helpers."""

from __future__ import annotations

import re
from typing import Any

import bcrypt


def hash_password(password: str) -> str:
    password_bytes = str(password or "").encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    if not password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(str(password).encode("utf-8"), str(hashed_password).encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    value = str(password or "")
    if len(value) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", value):
        warnings.append("Add an uppercase letter for stronger security.")
    if not re.search(r"[a-z]", value):
        warnings.append("Add a lowercase letter for stronger security.")
    if not re.search(r"\d", value):
        warnings.append("Add a number for stronger security.")
    return {"valid": not errors, "warnings": warnings, "errors": errors}
