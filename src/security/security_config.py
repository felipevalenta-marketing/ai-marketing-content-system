"""Security configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import os


def _env_flag(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(1, int(str(raw).strip()))
    except Exception:
        return default


@dataclass(frozen=True)
class SecurityConfig:
    enable_security_hardening: bool = field(default_factory=lambda: _env_flag("ENABLE_SECURITY_HARDENING", True))
    enable_security_headers: bool = field(default_factory=lambda: _env_flag("ENABLE_SECURITY_HEADERS", True))
    enable_rate_limiting: bool = field(default_factory=lambda: _env_flag("ENABLE_RATE_LIMITING", True))
    enable_rate_limit_test_mode: bool = field(default_factory=lambda: _env_flag("ENABLE_RATE_LIMIT_TEST_MODE", False))
    enable_secret_scanning: bool = field(default_factory=lambda: _env_flag("ENABLE_SECRET_SCANNING", True))
    enable_dependency_validation: bool = field(default_factory=lambda: _env_flag("ENABLE_DEPENDENCY_VALIDATION", True))
    enable_input_sanitization: bool = field(default_factory=lambda: _env_flag("ENABLE_INPUT_SANITIZATION", True))
    enable_output_sanitization: bool = field(default_factory=lambda: _env_flag("ENABLE_OUTPUT_SANITIZATION", True))
    request_size_limit_kb: int = field(default_factory=lambda: _env_int("REQUEST_SIZE_LIMIT_KB", 256))
    anonymous_rate_limit_per_hour: int = field(default_factory=lambda: _env_int("ANONYMOUS_RATE_LIMIT_PER_HOUR", 100))
    authenticated_rate_limit_per_hour: int = field(default_factory=lambda: _env_int("AUTHENTICATED_RATE_LIMIT_PER_HOUR", 1000))
    admin_rate_limit_per_hour: int = field(default_factory=lambda: _env_int("ADMIN_RATE_LIMIT_PER_HOUR", 5000))
    issuer: str = field(default_factory=lambda: os.getenv("JWT_ISSUER", "").strip())
    allowed_algorithms: tuple[str, ...] = ("HS256",)
    csp_policy: str = "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"


def build_security_configuration(app: Any | None = None) -> dict[str, Any]:
    config = SecurityConfig()
    app_config = getattr(getattr(app, "state", None), "config", None)
    environment = str(getattr(app_config, "environment", os.getenv("APP_ENV", "development"))).strip().lower()
    production = environment == "production"
    return {
        "security_enabled": config.enable_security_hardening,
        "security_headers_enabled": config.enable_security_headers,
        "rate_limiting_enabled": config.enable_rate_limiting,
        "rate_limit_test_mode_enabled": config.enable_rate_limit_test_mode,
        "secret_scanning_enabled": config.enable_secret_scanning,
        "dependency_validation_enabled": config.enable_dependency_validation,
        "input_sanitization_enabled": config.enable_input_sanitization,
        "output_sanitization_enabled": config.enable_output_sanitization,
        "request_size_limit_kb": config.request_size_limit_kb,
        "anonymous_rate_limit_per_hour": config.anonymous_rate_limit_per_hour,
        "authenticated_rate_limit_per_hour": config.authenticated_rate_limit_per_hour,
        "admin_rate_limit_per_hour": config.admin_rate_limit_per_hour,
        "issuer": config.issuer,
        "allowed_algorithms": list(config.allowed_algorithms),
        "environment": environment,
        "production_mode": production,
        "csp_policy": config.csp_policy,
        "permissions_policy": config.permissions_policy,
    }
