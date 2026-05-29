"""User profile normalization helpers."""

from __future__ import annotations

from typing import Any


def build_safe_user_profile(user: dict[str, Any]) -> dict[str, Any]:
    safe = dict(user or {})
    safe.pop("password_hash", None)
    safe.pop("password", None)
    role = str(safe.get("role", "viewer") or "viewer").strip().lower()
    safe["role"] = role or "viewer"
    permissions = safe.get("permissions", [])
    safe["permissions"] = list(permissions) if isinstance(permissions, list) else []
    return safe
