"""Health payload helpers for the API layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.cli.cli_config import build_module_presence
from src.api.api_config import ApiConfig


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_health_payload(config: ApiConfig | None = None) -> dict[str, Any]:
    config = config or ApiConfig()
    modules = build_module_presence()
    return {
        "status": "ok",
        "service": config.service_name,
        "environment": config.environment,
        "version": config.api_version,
        "timestamp": _timestamp(),
        "modules": {
            "api_layer": config.enable_api_layer,
            "frontend_demo": config.enable_frontend_demo,
            "pipeline": modules.get("src.pipeline", False),
            "workflow": modules.get("src.workflows", False),
            "analytics": modules.get("src.analytics", False),
            "brands": modules.get("src.brands", False),
            "reporting": modules.get("src.reporting", False),
            "storage": modules.get("src.storage", False),
        },
    }


def build_readiness_payload(app: Any | None = None) -> dict[str, Any]:
    config = getattr(getattr(app, "state", None), "config", None) or ApiConfig()
    services = getattr(getattr(app, "state", None), "services", {}) if app is not None else {}
    storage = services.get("storage") if isinstance(services, dict) else None
    storage_ready = bool(storage)
    routes_registered = bool(getattr(app, "routes", [])) if app is not None else True
    return {
        "status": "ok" if routes_registered and storage_ready else "warning",
        "environment": config.environment,
        "config_loaded": True,
        "storage_ready": storage_ready,
        "routes_registered": routes_registered,
        "timestamp": _timestamp(),
    }


def build_liveness_payload(app: Any | None = None) -> dict[str, Any]:
    config = getattr(getattr(app, "state", None), "config", None) or ApiConfig()
    return {
        "status": "ok",
        "service": config.service_name,
        "environment": config.environment,
        "timestamp": _timestamp(),
    }
