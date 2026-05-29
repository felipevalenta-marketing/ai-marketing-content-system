"""Health payload helpers for the API layer."""

from __future__ import annotations

from typing import Any

from src.cli.cli_config import build_module_presence
from src.api.api_config import ApiConfig


def build_health_payload() -> dict[str, Any]:
    config = ApiConfig()
    modules = build_module_presence()
    return {
        "status": "ok",
        "service": config.service_name,
        "version": config.api_version,
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
