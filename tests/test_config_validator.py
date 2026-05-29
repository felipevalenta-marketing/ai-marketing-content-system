from __future__ import annotations

from src.configuration.config_defaults import DEFAULT_ENVIRONMENT_CONFIG, DEFAULT_FEATURE_FLAGS, DEFAULT_LIMITS, DEFAULT_PLATFORM_CONFIG
from src.configuration.config_validator import validate_configuration
from src.configuration.module_registry import build_module_registry


def test_configuration_validator_accepts_default_configuration() -> None:
    result = validate_configuration(DEFAULT_PLATFORM_CONFIG, DEFAULT_FEATURE_FLAGS, DEFAULT_LIMITS, DEFAULT_ENVIRONMENT_CONFIG, build_module_registry())

    assert result["valid"] is True
    assert result["errors"] == []

