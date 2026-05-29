"""Default configuration values for the platform."""

from __future__ import annotations

from typing import Any


DEFAULT_PLATFORM_CONFIG: dict[str, Any] = {
    "platform_name": "AI Marketing Content System",
    "environment": "development",
    "version": "1.0.0",
    "maintenance_mode": False,
    "registration_enabled": True,
    "analytics_enabled": True,
    "storage_enabled": True,
    "workflow_enabled": True,
    "reporting_enabled": True,
}

DEFAULT_FEATURE_FLAGS: dict[str, bool] = {
    "analytics_dashboard": True,
    "workflow_execution": True,
    "markdown_reports": True,
    "multi_brand": True,
    "authentication": True,
    "rbac": True,
}

DEFAULT_LIMITS: dict[str, int] = {
    "max_brands": 100,
    "max_users": 1000,
    "max_reports": 10000,
    "max_workflows": 10000,
    "max_storage_records": 100000,
}

DEFAULT_MODULES: list[dict[str, Any]] = [
    {"module": "authentication", "enabled": True, "description": "Authentication and login flows."},
    {"module": "users", "enabled": True, "description": "User profile and account management."},
    {"module": "rbac", "enabled": True, "description": "Role-based access control."},
    {"module": "brands", "enabled": True, "description": "Multi-brand discovery and configuration."},
    {"module": "workflows", "enabled": True, "description": "Workflow orchestration and planning."},
    {"module": "analytics", "enabled": True, "description": "Executive analytics and dashboard summaries."},
    {"module": "reporting", "enabled": True, "description": "Reporting and export summaries."},
    {"module": "storage", "enabled": True, "description": "Local file-based persistence."},
    {"module": "campaigns", "enabled": True, "description": "Campaign composition and bundling."},
    {"module": "assets", "enabled": True, "description": "Asset coordination and asset bundles."},
]

DEFAULT_ENVIRONMENT_CONFIG: dict[str, Any] = {
    "environment": "development",
    "debug": True,
    "show_stack_traces": True,
}

