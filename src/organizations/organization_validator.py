"""Organization validation helpers."""

from __future__ import annotations

from typing import Any
import json

from src.reporting.report_metrics import safe_text

from .organization_registry import is_valid_organization_id, normalize_slug


VALID_ORG_STATUSES = {"active", "inactive", "suspended"}


def validate_organization(organization: dict[str, Any] | None) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    payload = dict(organization or {})
    organization_id = safe_text(payload.get("organization_id"), limit=120)
    name = safe_text(payload.get("name"), limit=160)
    slug = normalize_slug(payload.get("slug") or name)
    status = safe_text(payload.get("status", "active"), limit=40)
    if not is_valid_organization_id(organization_id):
        errors.append("Invalid organization_id.")
    if not name:
        errors.append("Organization name is required.")
    if not slug:
        errors.append("Organization slug is required.")
    if status not in VALID_ORG_STATUSES:
        errors.append("Invalid organization status.")
    try:
        json.dumps(payload, default=str)
    except Exception:
        errors.append("Organization payload must be JSON serializable.")
    if any(token in json.dumps(payload, default=str).lower() for token in ("openai_api_key", "jwt_secret", "password_hash", ".env")):
        warnings.append("Sensitive fields should not be exposed.")
    return {"valid": not errors, "warnings": warnings, "errors": errors}

