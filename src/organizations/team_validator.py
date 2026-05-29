"""Team validation helpers."""

from __future__ import annotations

from typing import Any
import json

from src.reporting.report_metrics import safe_text

from .organization_registry import is_valid_team_id, normalize_slug


VALID_TEAM_STATUSES = {"active", "inactive", "archived"}


def validate_team(team: dict[str, Any] | None, organization_exists: bool = True) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    payload = dict(team or {})
    team_id = safe_text(payload.get("team_id"), limit=120)
    name = safe_text(payload.get("name"), limit=160)
    slug = normalize_slug(payload.get("slug") or name)
    status = safe_text(payload.get("status", "active"), limit=40)
    if not organization_exists:
        errors.append("Organization does not exist.")
    if not is_valid_team_id(team_id):
        errors.append("Invalid team_id.")
    if not name:
        errors.append("Team name is required.")
    if not slug:
        errors.append("Team slug is required.")
    if status not in VALID_TEAM_STATUSES:
        errors.append("Invalid team status.")
    try:
        json.dumps(payload, default=str)
    except Exception:
        errors.append("Team payload must be JSON serializable.")
    return {"valid": not errors, "warnings": warnings, "errors": errors}

