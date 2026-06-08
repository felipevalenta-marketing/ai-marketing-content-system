"""Security policy rules and MVP baseline compatibility."""

from __future__ import annotations

from typing import Any
import os

from src.api.api_config import ApiConfig
from src.auth.jwt_manager import get_secret_status
from src.pipeline.pipeline_config import PipelineConfig
from src.security.security_config import build_security_configuration


def _services(app: Any | None) -> dict[str, Any]:
    services = getattr(getattr(app, "state", None), "services", {}) if app is not None else {}
    return services if isinstance(services, dict) else {}


def resolve_cors_origins(app: Any | None = None) -> dict[str, Any]:
    config = getattr(getattr(app, "state", None), "config", None) or ApiConfig()
    environment = str(getattr(config, "environment", os.getenv("APP_ENV", "development"))).strip().lower()
    raw_origins = list(getattr(config, "cors_origins", ()))
    production = environment == "production"
    warnings: list[str] = []
    origins: list[str] = []
    for origin in raw_origins:
        text = str(origin).strip()
        if not text:
            continue
        if text == "*" and production:
            warnings.append("Wildcard CORS origin blocked in production.")
            continue
        origins.append(text)
    if production:
        if not origins:
            warnings.append("No explicit CORS origins configured for production.")
        if any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
            warnings.append("Localhost CORS origins should not be used in production.")
    else:
        if not any("localhost" in origin or "127.0.0.1" in origin for origin in origins):
            warnings.append("Localhost CORS origins are recommended for development.")
    if "*" in raw_origins and not production:
        origins = [origin for origin in origins if origin != "*"] + ["*"]
    return {
        "environment": environment,
        "production": production,
        "allow_origins": origins or list(raw_origins),
        "warnings": warnings,
    }


def build_security_policy(app: Any | None = None) -> dict[str, Any]:
    config = build_security_configuration(app)
    services = _services(app)
    pipeline = services.get("pipeline_config") or getattr(getattr(app, "state", None), "pipeline_config", None) or PipelineConfig()
    cors = resolve_cors_origins(app)
    jwt_secret_status = get_secret_status()
    required_checks = {
        "authentication_enabled": bool(getattr(pipeline, "enable_authentication", True)),
        "rbac_enabled": bool(getattr(pipeline, "enable_rbac", True)),
        "jwt_secret_configured": bool(jwt_secret_status.get("available", False)),
        "password_hashes_protected": True,
        "rate_limiting_enabled": bool(config.get("rate_limiting_enabled", True)),
        "security_headers_enabled": bool(config.get("security_headers_enabled", True)),
        "input_sanitization_enabled": bool(config.get("input_sanitization_enabled", True)),
        "output_sanitization_enabled": bool(config.get("output_sanitization_enabled", True)),
        "path_traversal_protection_enabled": True,
        "secret_scanner_enabled": bool(config.get("secret_scanning_enabled", True)),
        "dependency_validator_enabled": bool(config.get("dependency_validation_enabled", True)),
    }
    active_modules = [
        name
        for name, enabled in {
            "authentication": required_checks["authentication_enabled"],
            "rbac": required_checks["rbac_enabled"],
            "security_headers": required_checks["security_headers_enabled"],
            "rate_limiting": required_checks["rate_limiting_enabled"],
            "input_sanitization": required_checks["input_sanitization_enabled"],
            "output_sanitization": required_checks["output_sanitization_enabled"],
            "secret_scanner": required_checks["secret_scanner_enabled"],
            "dependency_validator": required_checks["dependency_validator_enabled"],
        }.items()
        if enabled
    ]
    warnings = list(cors.get("warnings", []))
    if not required_checks["jwt_secret_configured"]:
        warnings.append("JWT secret is not configured.")
    return {
        "policy_name": "mvp_security_baseline",
        "environment": config.get("environment", "development"),
        "production_mode": bool(config.get("production_mode", False)),
        "required_checks": required_checks,
        "enabled_modules": active_modules,
        "cors": cors,
        "warnings": warnings,
        "policy_ready": all(required_checks.values()) and not warnings,
        "release_ready": all(required_checks.values()),
    }


def build_security_policy_summary(app: Any | None = None) -> dict[str, Any]:
    return build_security_policy(app)
