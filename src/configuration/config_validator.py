"""Validation helpers for configuration data."""

from __future__ import annotations

from typing import Any

from src.configuration.config_defaults import DEFAULT_ENVIRONMENT_CONFIG, DEFAULT_FEATURE_FLAGS, DEFAULT_LIMITS, DEFAULT_PLATFORM_CONFIG, DEFAULT_MODULES
from src.configuration.environment_config import normalize_environment


def validate_configuration(platform_config: dict[str, Any] | None, feature_flags: dict[str, Any] | None, limits: dict[str, Any] | None, environment_config: dict[str, Any] | None, module_registry: list[dict[str, Any]] | None) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []

    platform = dict(platform_config or {})
    features = dict(feature_flags or {})
    quota = dict(limits or {})
    environment = dict(environment_config or {})
    modules = list(module_registry or [])

    for key in DEFAULT_PLATFORM_CONFIG:
        if key not in platform:
            warnings.append(f"Platform config missing {key}.")
    for key, value in features.items():
        if not isinstance(value, bool):
            errors.append(f"Feature flag {key} must be boolean.")
    for key in DEFAULT_FEATURE_FLAGS:
        if key not in features:
            warnings.append(f"Feature flag missing: {key}")
    for key, value in quota.items():
        if not isinstance(value, int) or value < 0:
            errors.append(f"Limit {key} must be a non-negative integer.")
    if normalize_environment(environment.get("environment")) not in {"development", "staging", "production"}:
        errors.append("Invalid environment.")
    if environment.get("environment") == "production" and bool(environment.get("debug")):
        warnings.append("Production environment should disable debug mode.")
    module_names = {str(module.get("module", "")).strip() for module in modules if isinstance(module, dict)}
    for module in DEFAULT_MODULES:
        if module["module"] not in module_names:
            warnings.append(f"Module missing: {module['module']}")
    return {"valid": not errors, "warnings": warnings, "errors": errors}

