"""Safe configuration helpers for the API layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import os

from src.cli.cli_config import build_safe_config_summary


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


@dataclass(frozen=True)
class ApiConfig:
    enable_api_layer: bool = field(default_factory=lambda: _env_flag("ENABLE_API_LAYER", True))
    enable_frontend_demo: bool = field(default_factory=lambda: _env_flag("ENABLE_FRONTEND_DEMO", True))
    api_debug: bool = field(default_factory=lambda: _env_flag("API_DEBUG", False))
    api_title: str = "AI Marketing Content System API"
    api_version: str = "0.1.0"
    service_name: str = "ai-marketing-content-system"
    environment: str = field(default_factory=lambda: os.getenv("APP_ENV", "development").strip() or "development")
    api_base_url: str = "http://127.0.0.1:8000"
    frontend_root: str = "frontend"
    cors_origins: tuple[str, ...] = ("http://127.0.0.1:8000", "http://localhost:8000", "http://127.0.0.1:5500", "http://localhost:5500")


def build_api_config_summary() -> dict[str, Any]:
    config = ApiConfig()
    summary = build_safe_config_summary()
    summary.update(
        {
            "api_layer_enabled": config.enable_api_layer,
            "frontend_demo_enabled": config.enable_frontend_demo,
            "api_debug": config.api_debug,
            "api_base_url": config.api_base_url,
            "frontend_root": config.frontend_root,
            "cors_origins": list(config.cors_origins),
            "api_service_name": config.service_name,
            "api_version": config.api_version,
        }
    )
    return summary
