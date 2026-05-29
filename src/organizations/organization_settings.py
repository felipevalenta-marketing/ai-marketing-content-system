"""Organization settings helpers."""

from __future__ import annotations

from typing import Any

from src.configuration.config_defaults import DEFAULT_FEATURE_FLAGS, DEFAULT_LIMITS


def build_organization_settings(overrides: dict[str, Any] | None = None, config_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    config_defaults = dict(config_summary or {})
    config_limits = dict(config_defaults.get("limits", {})) if isinstance(config_defaults.get("limits", {}), dict) else {}
    config_features = dict(config_defaults.get("feature_flags", {})) if isinstance(config_defaults.get("feature_flags", {}), dict) else {}
    settings = {
        "default_brand": "wenzel_partner",
        "default_platform": "instagram",
        "default_language": "en",
        "timezone": "Europe/Madrid",
        "features": {
            "workflow_execution": config_features.get("workflow_execution", DEFAULT_FEATURE_FLAGS.get("workflow_execution", True)),
        },
        "limits": {
            "max_teams": config_limits.get("max_teams", 20),
            "max_members_per_organization": config_limits.get("max_members_per_organization", 100),
            "max_brands": config_limits.get("max_brands", DEFAULT_LIMITS.get("max_brands", 100)),
        },
    }
    if isinstance(overrides, dict):
        for key, value in overrides.items():
            if key in {"features", "limits"} and isinstance(value, dict):
                settings[key] = {**settings.get(key, {}), **value}
            elif value not in (None, ""):
                settings[key] = value
    return settings
