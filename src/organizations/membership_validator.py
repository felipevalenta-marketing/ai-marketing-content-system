"""Membership validation helpers."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_text

VALID_MEMBERSHIP_STATUSES = {"active", "inactive"}
VALID_ORG_ROLES = {"owner", "admin", "manager", "member", "viewer"}


def validate_membership(
    membership: dict[str, Any] | None,
    *,
    organization_exists: bool = True,
    team_exists: bool = True,
    user_exists: bool = True,
    existing_memberships: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    payload = dict(membership or {})
    role = safe_text(payload.get("role", "member"), limit=40).lower()
    if not organization_exists:
        errors.append("Organization does not exist.")
    if not user_exists:
        errors.append("User does not exist.")
    if payload.get("team_id") and not team_exists:
        errors.append("Team does not exist.")
    if role not in VALID_ORG_ROLES and role not in {"lead", "editor"}:
        errors.append("Invalid membership role.")
    if safe_text(payload.get("status", "active"), limit=40).lower() not in VALID_MEMBERSHIP_STATUSES:
        errors.append("Invalid membership status.")
    existing = existing_memberships or []
    duplicate = any(
        str(item.get("organization_id", "")) == str(payload.get("organization_id", ""))
        and str(item.get("user_id", "")) == str(payload.get("user_id", ""))
        and str(item.get("team_id", "")) == str(payload.get("team_id", ""))
        for item in existing
    )
    if duplicate:
        errors.append("Duplicate membership.")
    return {"valid": not errors, "warnings": warnings, "errors": errors}

