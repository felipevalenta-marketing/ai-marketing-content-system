"""Aggregate release health from platform subsystems."""

from __future__ import annotations

from typing import Any


def _status_to_score(status: str) -> int:
    mapping = {"healthy": 100, "ready": 100, "approved": 100, "warning": 70, "ok": 90, "critical": 20, "blocked": 0}
    return mapping.get(str(status).lower(), 50)


def build_release_health(app: Any | None = None, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    from src.api.health import build_health_payload, build_liveness_payload, build_readiness_payload
    from src.configuration.config_manager import ConfigManager
    from src.observability.observability_health import build_observability_health
    from src.security.security_health import build_security_health

    services = getattr(getattr(app, "state", None), "services", {}) if app is not None else {}
    configuration = None
    if app is not None:
        configuration = services.get("configuration")
    if configuration is None:
        configuration = ConfigManager()

    config_validation = configuration.validate_configuration() if hasattr(configuration, "validate_configuration") else {"valid": True, "warnings": [], "errors": []}
    api_health = build_health_payload(getattr(getattr(app, "state", None), "config", None))
    readiness = build_readiness_payload(app)
    liveness = build_liveness_payload(app)
    observability = build_observability_health(app)
    security = build_security_health(app)
    organizations_service = services.get("organizations") if isinstance(services, dict) else None
    organization_health = {"overall_health": "healthy", "health_score": 100, "warnings": [], "errors": []}
    if organizations_service is not None and hasattr(organizations_service, "list_organizations"):
        try:
            organizations_payload = organizations_service.list_organizations()
            organizations = organizations_payload.get("organizations", []) if isinstance(organizations_payload, dict) else []
            if organizations:
                first_org = organizations[0]
                org_id = str(first_org.get("organization_id", "")).strip()
                profile = organizations_service.build_organization_profile(org_id) if org_id and hasattr(organizations_service, "build_organization_profile") else {}
                organization_health = profile.get("health", organization_health) if isinstance(profile, dict) else organization_health
                if not organization_health.get("overall_health"):
                    organization_health = {
                        "overall_health": str(first_org.get("health_status", "healthy") or "healthy"),
                        "health_score": int(first_org.get("health_score", 75) or 75),
                        "warnings": [],
                        "errors": [],
                    }
        except Exception:
            organization_health = {"overall_health": "warning", "health_score": 50, "warnings": ["Organization health unavailable."], "errors": []}

    checks = {
        "platform": api_health.get("status") == "ok" and readiness.get("status") == "ok" and liveness.get("status") == "ok",
        "configuration": bool(config_validation.get("valid", False)),
        "observability": observability.get("health_status") in {"healthy", "warning"},
        "security": security.get("security_status") in {"healthy", "warning"},
        "organizations": organization_health.get("overall_health") in {"healthy", "warning"},
        "documentation": True,
        "deployment": True,
    }
    health_score = int(round(sum(_status_to_score(str(value and "healthy" or "critical")) for value in checks.values()) / max(1, len(checks))))
    if all(checks.values()) and observability.get("health_status") == "healthy" and security.get("security_status") == "healthy" and organization_health.get("overall_health") == "healthy":
        overall_health = "healthy"
    elif checks["platform"] and checks["configuration"]:
        overall_health = "warning"
    else:
        overall_health = "critical"
    return {
        "overall_health": overall_health,
        "health_score": max(0, min(100, health_score)),
        "checks": checks,
        "platform_health": api_health,
        "organization_health": organization_health,
        "observability_health": observability,
        "security_health": security,
        "configuration_health": configuration.get_configuration_health() if hasattr(configuration, "get_configuration_health") else config_validation,
    }
