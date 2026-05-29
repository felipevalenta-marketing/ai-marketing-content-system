"""User validation helpers."""

from __future__ import annotations

import re
from typing import Any


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def validate_email(email: str) -> dict[str, Any]:
    value = normalize_email(email)
    errors: list[str] = []
    if not value:
        errors.append("Email is required.")
    elif not EMAIL_PATTERN.match(value):
        errors.append("Email format is invalid.")
    return {"valid": not errors, "warnings": [], "errors": errors}


def validate_user_status(status: str) -> dict[str, Any]:
    allowed = {"active", "inactive", "suspended"}
    value = str(status or "").strip().lower()
    if value not in allowed:
        return {"valid": False, "warnings": [], "errors": ["Invalid user status."]}
    return {"valid": True, "warnings": [], "errors": []}
