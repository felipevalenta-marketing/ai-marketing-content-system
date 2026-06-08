"""Centralized SaaS configuration manager."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import os

from src.brands.brand_manager import BrandManager
from src.configuration.config_defaults import DEFAULT_ENVIRONMENT_CONFIG, DEFAULT_FEATURE_FLAGS, DEFAULT_LIMITS, DEFAULT_PLATFORM_CONFIG
from src.configuration.config_loader import load_json, save_json
from src.configuration.config_registry import build_configuration_registry
from src.configuration.config_result import build_summary_result, build_success_result, build_update_result, build_validation_result
from src.configuration.config_validator import validate_configuration
from src.configuration.environment_config import build_environment_config, normalize_environment
from src.configuration.feature_flags import FeatureFlagManager
from src.configuration.module_registry import build_module_registry


def _env_bool(name: str) -> bool | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    return None


def _env_text(name: str) -> str | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def _is_sensitive_key(key: str) -> bool:
    normalized = str(key or "").strip().lower()
    if normalized.endswith("_present"):
        return False
    return any(token in normalized for token in ("api_key", "password", "secret", "credential", "token", "env"))


def _sanitize_config_value(value: Any, key: str = "") -> Any:
    normalized_key = str(key or "").strip().lower()
    if _is_sensitive_key(normalized_key):
        return "[redacted]"
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for item_key, item_value in value.items():
            cleaned_key = str(item_key).strip()
            if _is_sensitive_key(cleaned_key):
                sanitized[cleaned_key] = "[redacted]"
            else:
                sanitized[cleaned_key] = _sanitize_config_value(item_value, cleaned_key)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_config_value(item, normalized_key) for item in value]
    return value


class ConfigManager:
    def __init__(self, config_root: str = "data/config", brand_manager: BrandManager | None = None) -> None:
        self.config_root = Path(config_root)
        self.brand_manager = brand_manager
        self.platform_path = self.config_root / "platform.json"
        self.features_path = self.config_root / "features.json"
        self._registry = build_configuration_registry()
        self._platform_config = self._load_platform_config()
        self._feature_manager = FeatureFlagManager(self._load_feature_flags())

    def _load_platform_config(self) -> dict[str, Any]:
        payload = load_json(self.platform_path, DEFAULT_PLATFORM_CONFIG)
        platform = dict(DEFAULT_PLATFORM_CONFIG)
        platform.update({key: value for key, value in payload.items() if value not in (None, "")})
        env_overrides = {
            "platform_name": _env_text("PLATFORM_NAME"),
            "environment": _env_text("APP_ENV") or _env_text("ENVIRONMENT"),
            "version": _env_text("PLATFORM_VERSION"),
            "maintenance_mode": _env_bool("MAINTENANCE_MODE"),
            "registration_enabled": _env_bool("REGISTRATION_ENABLED"),
            "analytics_enabled": _env_bool("ANALYTICS_ENABLED"),
            "storage_enabled": _env_bool("STORAGE_ENABLED"),
            "workflow_enabled": _env_bool("WORKFLOW_ENABLED"),
            "reporting_enabled": _env_bool("REPORTING_ENABLED"),
        }
        for key, value in env_overrides.items():
            if value is not None:
                platform[key] = value
        platform["environment"] = normalize_environment(platform.get("environment"))
        return platform

    def _load_feature_flags(self) -> dict[str, bool]:
        payload = load_json(self.features_path, DEFAULT_FEATURE_FLAGS)
        flags = {str(key): bool(value) for key, value in DEFAULT_FEATURE_FLAGS.items()}
        for key, value in payload.items():
            flags[str(key)] = bool(value)
        for key in list(flags):
            env_value = _env_bool(str(key).upper())
            if env_value is not None:
                flags[str(key)] = env_value
        return flags

    def _load_module_registry(self) -> list[dict[str, Any]]:
        modules = build_module_registry()
        for module in modules:
            module_name = str(module.get("module", "")).strip()
            if not module_name:
                continue
            env_value = _env_bool(f"MODULE_{module_name.upper()}")
            if env_value is not None:
                module["enabled"] = env_value
        return modules

    def _save_feature_flags(self) -> None:
        save_json(self.features_path, self._feature_manager.list_flags())

    def get_platform_config(self) -> dict[str, Any]:
        platform = _sanitize_config_value(dict(self._platform_config))
        platform.setdefault("metadata", {})
        platform["metadata"] = {
            **dict(platform.get("metadata", {})),
            "updated_at": platform.get("metadata", {}).get("updated_at", datetime.now(timezone.utc).isoformat()),
        }
        return platform

    def get_feature_flags(self) -> dict[str, bool]:
        return self._feature_manager.list_flags()

    def get_module_registry(self) -> list[dict[str, Any]]:
        return self._load_module_registry()

    def get_limits(self) -> dict[str, int]:
        limits = dict(DEFAULT_LIMITS)
        env_limits = {
            "max_brands": os.getenv("MAX_BRANDS"),
            "max_users": os.getenv("MAX_USERS"),
            "max_reports": os.getenv("MAX_REPORTS"),
            "max_workflows": os.getenv("MAX_WORKFLOWS"),
            "max_storage_records": os.getenv("MAX_STORAGE_RECORDS"),
        }
        for key, value in env_limits.items():
            if value is None:
                continue
            try:
                limits[key] = max(0, int(str(value).strip()))
            except Exception:
                continue
        return limits

    def get_environment_config(self) -> dict[str, Any]:
        platform = self.get_platform_config()
        return build_environment_config(platform.get("environment"))

    def get_brand_overrides(self, brand_id: str | None = None) -> dict[str, Any]:
        if not self.brand_manager or not brand_id:
            return {}
        profile = self.brand_manager.get_brand(brand_id)
        if not isinstance(profile, dict) or not profile.get("success"):
            return {}
        return {
            "brand_id": profile.get("brand_id", ""),
            "defaults": dict(profile.get("defaults", {})),
            "display_name": profile.get("display_name", ""),
        }

    def get_system_summary(self) -> dict[str, Any]:
        platform = self.get_platform_config()
        features = self.get_feature_flags()
        modules = self.get_module_registry()
        limits = self.get_limits()
        environment = self.get_environment_config()
        health = self.get_configuration_health()
        ci_configuration = {
            "enable_ci_security_checks": _env_bool("ENABLE_CI_SECURITY_CHECKS") if _env_bool("ENABLE_CI_SECURITY_CHECKS") is not None else False,
            "enable_release_validation": _env_bool("ENABLE_RELEASE_VALIDATION") if _env_bool("ENABLE_RELEASE_VALIDATION") is not None else False,
            "enable_docker_validation": _env_bool("ENABLE_DOCKER_VALIDATION") if _env_bool("ENABLE_DOCKER_VALIDATION") is not None else False,
        }
        summary = {
            "platform_config": platform,
            "feature_flags": features,
            "modules": modules,
            "limits": limits,
            "environment": environment,
            "configuration_health": health,
            "ci_configuration": ci_configuration,
            "release_configuration": {
                "enable_release_validation": _env_bool("ENABLE_RELEASE_VALIDATION") if _env_bool("ENABLE_RELEASE_VALIDATION") is not None else False,
                "enable_mvp_acceptance": _env_bool("ENABLE_MVP_ACCEPTANCE") if _env_bool("ENABLE_MVP_ACCEPTANCE") is not None else True,
                "enable_readiness_scoring": _env_bool("ENABLE_READINESS_SCORING") if _env_bool("ENABLE_READINESS_SCORING") is not None else True,
                "enable_release_certification": _env_bool("ENABLE_RELEASE_CERTIFICATION") if _env_bool("ENABLE_RELEASE_CERTIFICATION") is not None else True,
                "enable_maturity_scoring": _env_bool("ENABLE_MATURITY_SCORING") if _env_bool("ENABLE_MATURITY_SCORING") is not None else True,
            },
            "security_configuration": {
                "enable_security_hardening": _env_bool("ENABLE_SECURITY_HARDENING") if _env_bool("ENABLE_SECURITY_HARDENING") is not None else True,
                "enable_security_headers": _env_bool("ENABLE_SECURITY_HEADERS") if _env_bool("ENABLE_SECURITY_HEADERS") is not None else True,
                "enable_rate_limiting": _env_bool("ENABLE_RATE_LIMITING") if _env_bool("ENABLE_RATE_LIMITING") is not None else True,
                "enable_secret_scanning": _env_bool("ENABLE_SECRET_SCANNING") if _env_bool("ENABLE_SECRET_SCANNING") is not None else True,
                "enable_dependency_validation": _env_bool("ENABLE_DEPENDENCY_VALIDATION") if _env_bool("ENABLE_DEPENDENCY_VALIDATION") is not None else True,
                "enable_input_sanitization": _env_bool("ENABLE_INPUT_SANITIZATION") if _env_bool("ENABLE_INPUT_SANITIZATION") is not None else True,
                "enable_output_sanitization": _env_bool("ENABLE_OUTPUT_SANITIZATION") if _env_bool("ENABLE_OUTPUT_SANITIZATION") is not None else True,
            },
            "enabled_modules": [module for module in modules if module.get("enabled")],
            "enabled_flags": [flag for flag, enabled in features.items() if enabled],
            "organizations_enabled": _env_bool("ENABLE_ORGANIZATIONS") if _env_bool("ENABLE_ORGANIZATIONS") is not None else True,
            "teams_enabled": _env_bool("ENABLE_TEAMS") if _env_bool("ENABLE_TEAMS") is not None else True,
            "max_organizations": int(os.getenv("MAX_ORGANIZATIONS", "100") or 100),
            "max_teams": int(os.getenv("MAX_TEAMS", "500") or 500),
            "max_members_per_organization": int(os.getenv("MAX_MEMBERS_PER_ORGANIZATION", "1000") or 1000),
            "brand_overrides": self.get_brand_overrides(self._platform_config.get("default_brand")),
            "api_key_present": bool(os.getenv("OPENAI_API_KEY", "").strip()),
            "metadata": {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "config_root": str(self.config_root),
            },
        }
        return summary

    def update_feature_flag(self, flag: str, enabled: bool) -> dict[str, Any]:
        normalized = str(flag or "").strip()
        if not normalized:
            return build_update_result(flag="", value=None, errors=["Feature flag is required."])
        if normalized not in self.get_feature_flags():
            return build_update_result(flag=normalized, value=None, errors=["Invalid feature flag."])
        self._feature_manager.update(normalized, bool(enabled))
        self._save_feature_flags()
        return build_update_result(flag=normalized, value=bool(enabled), metadata={"updated_at": datetime.now(timezone.utc).isoformat()})

    def get_configuration_health(self) -> dict[str, Any]:
        validation = self.validate_configuration()
        enabled_modules = sum(1 for module in self.get_module_registry() if module.get("enabled"))
        enabled_flags = sum(1 for enabled in self.get_feature_flags().values() if enabled)
        warnings = list(validation.get("warnings", []))
        errors = list(validation.get("errors", []))
        valid = bool(validation.get("valid", False))
        status = "healthy" if valid and not warnings else "warning" if not errors else "critical"
        return {
            "enabled_modules": enabled_modules,
            "enabled_flags": enabled_flags,
            "environment": self.get_environment_config().get("environment", "development"),
            "valid": valid,
            "status": status,
            "warnings": warnings,
            "errors": errors,
        }

    def validate_configuration(self) -> dict[str, Any]:
        return validate_configuration(self.get_platform_config(), self.get_feature_flags(), self.get_limits(), self.get_environment_config(), self.get_module_registry())
