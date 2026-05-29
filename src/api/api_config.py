"""Safe configuration helpers for the API layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import os

from src.cli.cli_config import build_safe_config_summary
from src.configuration.config_manager import ConfigManager
from src.pipeline.pipeline_config import PipelineConfig


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return default


def _env_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value.strip())
    except (TypeError, ValueError):
        return default


def _env_csv(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    values = tuple(item.strip() for item in raw_value.split(",") if item.strip())
    return values or default


@dataclass(frozen=True)
class ApiConfig:
    enable_api_layer: bool = field(default_factory=lambda: _env_flag("ENABLE_API_LAYER", True))
    enable_frontend_demo: bool = field(default_factory=lambda: _env_flag("ENABLE_FRONTEND_DEMO", True))
    api_debug: bool = field(default_factory=lambda: _env_flag("API_DEBUG", False))
    api_title: str = "AI Marketing Content System API"
    api_version: str = "0.1.0"
    service_name: str = "ai-marketing-content-system"
    environment: str = field(default_factory=lambda: os.getenv("APP_ENV", "development").strip() or "development")
    api_base_url: str = field(default_factory=lambda: os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1").strip() or "127.0.0.1")
    api_port: int = field(default_factory=lambda: _env_int("API_PORT", 8000))
    frontend_root: str = "frontend"
    cors_origins: tuple[str, ...] = field(default_factory=lambda: _env_csv("CORS_ORIGINS", ("http://127.0.0.1:5173", "http://localhost:5173", "http://localhost:3000")))


def build_api_config_summary() -> dict[str, Any]:
    config = ApiConfig()
    pipeline_config = PipelineConfig()
    summary = build_safe_config_summary()
    config_manager = ConfigManager()
    jwt_secret_present = bool(os.getenv("JWT_SECRET_KEY", "").strip())
    summary.update(
        {
            "api_layer_enabled": config.enable_api_layer,
            "frontend_demo_enabled": config.enable_frontend_demo,
            "api_debug": config.api_debug,
            "api_base_url": config.api_base_url,
            "api_host": config.api_host,
            "api_port": config.api_port,
            "frontend_root": config.frontend_root,
            "cors_origins": list(config.cors_origins),
            "api_service_name": config.service_name,
            "api_version": config.api_version,
            "enable_authentication": pipeline_config.enable_authentication,
            "jwt_expiration_hours": pipeline_config.jwt_expiration_hours,
            "user_storage_path": pipeline_config.user_storage_path,
            "jwt_secret_present": jwt_secret_present,
            "warnings": ([] if jwt_secret_present else ["JWT secret is not configured. Authentication will remain disabled until JWT_SECRET_KEY is provided."]),
            "configuration": config_manager.get_system_summary(),
            "configuration_health": config_manager.get_configuration_health(),
        }
    )
    return summary
