"""Registry helpers for configuration values."""

from __future__ import annotations

from typing import Any

from src.configuration.config_defaults import DEFAULT_ENVIRONMENT_CONFIG, DEFAULT_FEATURE_FLAGS, DEFAULT_LIMITS, DEFAULT_MODULES, DEFAULT_PLATFORM_CONFIG


def build_configuration_registry() -> dict[str, Any]:
    return {
        "platform": dict(DEFAULT_PLATFORM_CONFIG),
        "features": dict(DEFAULT_FEATURE_FLAGS),
        "limits": dict(DEFAULT_LIMITS),
        "modules": [dict(item) for item in DEFAULT_MODULES],
        "environment": dict(DEFAULT_ENVIRONMENT_CONFIG),
    }

