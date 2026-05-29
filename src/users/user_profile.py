"""User profile normalization helpers."""

from __future__ import annotations

from typing import Any


def build_safe_user_profile(user: dict[str, Any]) -> dict[str, Any]:
    safe = dict(user or {})
    safe.pop("password_hash", None)
    safe.pop("password", None)
    return safe
