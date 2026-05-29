"""Configuration contracts."""

from __future__ import annotations

from typing import Any


PLATFORM_CONFIG_CONTRACT: dict[str, Any] = {
    "platform_name": "AI Marketing Content System",
    "environment": "development",
    "version": "1.0.0",
    "maintenance_mode": False,
    "registration_enabled": True,
    "analytics_enabled": True,
    "storage_enabled": True,
    "workflow_enabled": True,
    "reporting_enabled": True,
    "metadata": {},
}

FEATURE_FLAGS_CONTRACT: dict[str, bool] = {
    "analytics_dashboard": True,
    "workflow_execution": True,
    "markdown_reports": True,
    "multi_brand": True,
    "authentication": True,
    "rbac": True,
}

LIMITS_CONTRACT: dict[str, int] = {
    "max_brands": 100,
    "max_users": 1000,
    "max_reports": 10000,
    "max_workflows": 10000,
    "max_storage_records": 100000,
}

MODULE_REGISTRY_CONTRACT: list[dict[str, Any]] = []

ENVIRONMENT_CONFIG_CONTRACT: dict[str, Any] = {
    "environment": "development",
    "debug": True,
    "show_stack_traces": True,
}

API_RESPONSE_CONTRACT: dict[str, Any] = {"success": True, "data": {}, "warnings": [], "errors": [], "metadata": {}}

