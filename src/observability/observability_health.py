"""Global observability health and status summaries."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.api.health import build_liveness_payload, build_readiness_payload
from src.observability.metrics_registry import get_metrics_registry
from src.observability.runtime_monitor import build_runtime_diagnostics
from src.observability.storage_monitor import build_storage_observability
from src.observability.workflow_monitor import get_workflow_monitor


def _services(app: Any | None) -> dict[str, Any]:
    services = getattr(getattr(app, "state", None), "services", {}) if app is not None else {}
    return services if isinstance(services, dict) else {}


def build_observability_configuration(app: Any | None = None) -> dict[str, bool]:
    services = _services(app)
    pipeline_config = services.get("pipeline_config")
    if pipeline_config is None and app is not None:
        pipeline_config = getattr(getattr(app, "state", None), "pipeline_config", None)
    if pipeline_config is None:
        from src.api.api_config import ApiConfig

        config = ApiConfig()
    else:
        config = pipeline_config
    return {
        "observability_enabled": bool(getattr(config, "enable_observability", True)),
        "request_logging_enabled": bool(getattr(config, "enable_request_logging", True)),
        "error_tracking_enabled": bool(getattr(config, "enable_error_tracking", True)),
        "runtime_metrics_enabled": bool(getattr(config, "enable_runtime_metrics", True)),
        "workflow_monitoring_enabled": bool(getattr(config, "enable_workflow_monitoring", True)),
    }


def get_system_status_summary(app: Any | None = None) -> dict[str, str]:
    services = _services(app)
    storage = services.get("storage")
    auth = services.get("auth")
    rbac = services.get("rbac")
    brands = services.get("brands")
    organizations = services.get("organizations")
    workflow = services.get("workflow")
    analytics = services.get("analytics")
    if services.get("configuration") is None:
        from src.configuration.config_manager import ConfigManager

        configuration = ConfigManager()
    else:
        configuration = services.get("configuration")

    config_validation = configuration.validate_configuration() if hasattr(configuration, "validate_configuration") else {"valid": True, "warnings": [], "errors": []}
    storage_health = build_storage_observability(storage)
    workflow_status = get_workflow_monitor().get_metrics()
    observability_enabled = build_observability_configuration(app).get("observability_enabled", True)

    summary = {
        "api": "healthy",
        "storage": "healthy" if storage_health.get("storage_root_exists") and storage_health.get("storage_root_writable") else "warning",
        "auth": "healthy" if auth is not None else "warning",
        "rbac": "healthy" if rbac is not None else "warning",
        "brands": "healthy" if brands is not None else "warning",
        "organizations": "healthy" if organizations is not None else "warning",
        "workflows": "healthy" if workflow is not None or workflow_status.get("total_workflow_runs", 0) >= 0 else "warning",
        "analytics": "healthy" if analytics is not None else "warning",
        "configuration": "healthy" if config_validation.get("valid", True) else "critical",
        "observability": "healthy" if observability_enabled else "warning",
    }
    return summary


def build_observability_health(app: Any | None = None) -> dict[str, Any]:
    from src.api.api_config import ApiConfig

    config = getattr(getattr(app, "state", None), "config", None) or ApiConfig()
    services = _services(app)
    storage = services.get("storage")
    auth = services.get("auth")
    rbac = services.get("rbac")
    workflow = services.get("workflow")
    analytics = services.get("analytics")
    if services.get("configuration") is None:
        from src.configuration.config_manager import ConfigManager

        configuration = ConfigManager()
    else:
        configuration = services.get("configuration")
    config_validation = configuration.validate_configuration() if hasattr(configuration, "validate_configuration") else {"valid": True, "warnings": [], "errors": []}
    readiness = build_readiness_payload(app)
    liveness = build_liveness_payload(app)
    runtime = build_runtime_diagnostics(app)
    storage_health = build_storage_observability(storage)
    workflow_health = get_workflow_monitor().get_metrics() if workflow is not None else get_workflow_monitor().get_metrics()
    metrics = get_metrics_registry().get_metrics()
    frontend_build = Path("frontend/dist").exists()
    observability_config = build_observability_configuration(app)
    system_status = get_system_status_summary(app)

    checks = {
        "api": {"status": "healthy" if liveness.get("status") == "ok" else "warning", "detail": "API process is running."},
        "configuration": {"status": "healthy" if config_validation.get("valid", True) else "critical", "detail": "Configuration loaded.", "warnings": list(config_validation.get("warnings", [])), "errors": list(config_validation.get("errors", []))},
        "storage": {"status": "healthy" if storage_health.get("storage_root_exists") and storage_health.get("storage_root_writable") else "warning", "detail": "Storage root checked."},
        "authentication": {"status": "healthy" if auth is not None else "warning", "detail": "Authentication service loaded."},
        "rbac": {"status": "healthy" if rbac is not None else "warning", "detail": "RBAC service loaded."},
        "workflows": {"status": "healthy" if workflow is not None else "warning", "detail": "Workflow service loaded.", "workflow_runs": workflow_health.get("total_workflow_runs", 0)},
        "analytics": {"status": "healthy" if analytics is not None else "warning", "detail": "Analytics service loaded."},
        "frontend_build": {"status": "healthy" if frontend_build else "warning", "detail": "Frontend production build present."},
        "environment": {"status": "healthy", "detail": config.environment},
    }

    warnings: list[str] = []
    errors: list[str] = []
    if not observability_config["observability_enabled"]:
        warnings.append("Observability is disabled.")
    if not storage_health.get("storage_root_exists"):
        warnings.append("Storage root is missing.")
    if not storage_health.get("storage_root_writable"):
        warnings.append("Storage root is not writable.")
    if not config_validation.get("valid", True):
        errors.extend(list(config_validation.get("errors", [])))

    status_score = 100
    factors = {
        "logging_enabled": observability_config["request_logging_enabled"],
        "metrics_available": bool(metrics),
        "health_checks_passing": readiness.get("status") == "ok" and liveness.get("status") == "ok",
        "request_logging_active": observability_config["request_logging_enabled"],
        "error_tracking_active": observability_config["error_tracking_enabled"],
        "runtime_monitoring_active": observability_config["runtime_metrics_enabled"],
        "workflow_monitoring_active": observability_config["workflow_monitoring_enabled"],
    }
    deductions = {
        "logging_enabled": 10,
        "metrics_available": 10,
        "health_checks_passing": 20,
        "request_logging_active": 10,
        "error_tracking_active": 10,
        "runtime_monitoring_active": 10,
        "workflow_monitoring_active": 10,
    }
    for factor, enabled in factors.items():
        if not enabled:
            status_score -= deductions[factor]
    if warnings:
        status_score -= min(15, len(warnings) * 5)
    if errors:
        status_score -= min(30, len(errors) * 10)
    health_score = max(0, min(100, status_score))
    if health_score >= 85 and not errors:
        health_status = "healthy"
    elif health_score >= 60:
        health_status = "warning"
    else:
        health_status = "critical"

    return {
        "health_score": health_score,
        "health_status": health_status,
        "warnings": warnings,
        "errors": errors,
        "status": health_status,
        "checks": checks,
        "system_status": system_status,
        "configuration": observability_config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sections": {
            "readiness": readiness,
            "liveness": liveness,
            "runtime": runtime,
            "storage": storage_health,
            "workflows": workflow_health,
            "metrics": metrics,
        },
    }
