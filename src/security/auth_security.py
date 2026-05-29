"""Authentication hardening helpers."""

from __future__ import annotations

from typing import Any

from src.reports.markdown_utils import safe_text


def build_auth_security_summary(user: dict[str, Any] | None = None, token_result: dict[str, Any] | None = None) -> dict[str, Any]:
    user = dict(user or {})
    token_result = dict(token_result or {})
    status = str(user.get("status", "unknown")).lower()
    role = str(user.get("role", "viewer")).lower()
    allowed = bool(token_result.get("valid", token_result.get("success", False)))
    warnings: list[str] = []
    errors: list[str] = []
    if role == "disabled":
        errors.append("Disabled users are blocked.")
        allowed = False
    if status not in {"active", "unknown"}:
        errors.append("Inactive users are blocked.")
        allowed = False
    if token_result and not token_result.get("valid", token_result.get("success", False)):
        errors.extend([str(item) for item in token_result.get("errors", []) if str(item).strip()])
    return {
        "allowed": allowed,
        "user_id": safe_text(user.get("user_id", ""), limit=120),
        "email": safe_text(user.get("email", ""), limit=120),
        "status": status,
        "role": role,
        "warnings": warnings,
        "errors": errors,
    }

