"""Security health scoring and summaries."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import os

from src.security.dependency_validator import validate_dependencies
from src.security.output_sanitizer import sanitize_output
from src.security.path_security import validate_path
from src.security.security_events import build_security_event_summary
from src.security.security_policy import build_security_policy
from src.security.secret_scanner import scan_repository
from src.security.security_config import build_security_configuration


def get_system_status_summary(app: Any | None = None) -> dict[str, str]:
    from src.observability.observability_health import get_system_status_summary as get_observability_summary

    summary = dict(get_observability_summary(app))
    security = "warning"
    services = getattr(getattr(app, "state", None), "services", {}) if app is not None else {}
    security_service = services.get("security") if isinstance(services, dict) else None
    if security_service is not None:
        status_payload = security_service.get_security_status(app=app) if hasattr(security_service, "get_security_status") else {}
        status = str((status_payload or {}).get("security_status") or (status_payload or {}).get("status") or "warning").lower()
        security = status if status in {"healthy", "warning", "critical"} else "warning"
    summary["security"] = security
    return summary


def build_security_baseline(app: Any | None = None) -> dict[str, Any]:
    config = build_security_configuration(app)
    policy = build_security_policy(app)
    jwt_secret = str(os.getenv("JWT_SECRET_KEY", "")).strip()
    checks = {
        "authentication_enabled": bool(policy.get("required_checks", {}).get("authentication_enabled", False)),
        "rbac_enabled": bool(policy.get("required_checks", {}).get("rbac_enabled", False)),
        "jwt_secret_configured": bool(jwt_secret),
        "password_hashes_protected": sanitize_output({"password_hash": "example"}).get("password_hash") == "[redacted]",
        "rate_limiting_enabled": bool(config.get("rate_limiting_enabled", True)),
        "security_headers_enabled": bool(config.get("security_headers_enabled", True)),
        "input_sanitization_enabled": bool(config.get("input_sanitization_enabled", True)),
        "output_sanitization_enabled": bool(config.get("output_sanitization_enabled", True)),
        "path_traversal_protection_enabled": not validate_path("../traverse").get("valid", True),
        "secret_scanner_enabled": bool(config.get("secret_scanning_enabled", True)),
        "dependency_validator_enabled": bool(config.get("dependency_validation_enabled", True)),
    }
    warnings = list(policy.get("warnings", []))
    errors: list[str] = []
    if not checks["jwt_secret_configured"]:
        warnings.append("JWT secret is missing.")
    if not policy.get("cors", {}).get("allow_origins"):
        warnings.append("No CORS origins configured.")
    baseline_score = int(round((sum(1 for value in checks.values() if value) / max(1, len(checks))) * 100))
    baseline_ready = all(checks.values()) and not errors
    if baseline_score >= 85 and not errors:
        status = "healthy"
    elif baseline_score >= 60:
        status = "warning"
    else:
        status = "critical"
    return {
        "baseline_ready": baseline_ready,
        "baseline_score": baseline_score,
        "baseline_status": status,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
        "policy": policy,
    }


def build_security_health(app: Any | None = None, *, findings: dict[str, Any] | None = None, dependencies: dict[str, Any] | None = None) -> dict[str, Any]:
    config = build_security_configuration(app)
    repo_findings = findings or scan_repository()
    dependency_report = dependencies or validate_dependencies()
    warnings = list(repo_findings.get("warnings", [])) + list(dependency_report.get("warnings", []))
    errors = list(repo_findings.get("errors", [])) + list(dependency_report.get("errors", []))
    baseline = build_security_baseline(app)
    warnings.extend(list(baseline.get("warnings", [])))
    factors = {
        "auth_security": bool(config.get("security_enabled", True)),
        "rbac_security": bool(config.get("security_enabled", True)),
        "jwt_security": bool(config.get("security_enabled", True)),
        "headers_enabled": bool(config.get("security_headers_enabled", True)),
        "rate_limiting_enabled": bool(config.get("rate_limiting_enabled", True)),
        "secret_scanning": bool(config.get("secret_scanning_enabled", True)),
        "dependency_validation": bool(config.get("dependency_validation_enabled", True)) and bool(dependency_report.get("dependencies_valid", False)),
        "path_protection": True,
        "observability_security": True,
    }
    deductions = {
        "auth_security": 10,
        "rbac_security": 10,
        "jwt_security": 10,
        "headers_enabled": 10,
        "rate_limiting_enabled": 10,
        "secret_scanning": 10,
        "dependency_validation": 15,
        "path_protection": 10,
        "observability_security": 5,
    }
    score = 100
    for factor, enabled in factors.items():
        if not enabled:
            score -= deductions[factor]
    score -= min(15, len(warnings) * 3)
    score -= min(40, len(errors) * 10)
    score = max(0, min(100, score))
    if score >= 85 and not errors:
        status = "healthy"
    elif score >= 60:
        status = "warning"
    else:
        status = "critical"
    recommendations: list[str] = []
    if not config.get("security_headers_enabled", True):
        recommendations.append("Enable security headers.")
    if not config.get("rate_limiting_enabled", True):
        recommendations.append("Enable rate limiting.")
    if errors:
        recommendations.append("Resolve security findings before release.")
    return {
        "security_score": score,
        "security_status": status,
        "baseline_ready": bool(baseline.get("baseline_ready", False)),
        "baseline_score": int(baseline.get("baseline_score", 0)),
        "baseline_status": baseline.get("baseline_status", "critical"),
        "warnings": warnings,
        "recommendations": recommendations,
        "status": status,
        "checks": factors,
        "configuration": config,
        "findings": repo_findings.get("findings", []),
        "dependencies": dependency_report,
        "policy": baseline.get("policy", {}),
        "recent_security_warnings": build_security_event_summary(limit=10).get("recent_security_warnings", []),
        "security_ready": status == "healthy" and not errors and bool(baseline.get("baseline_ready", False)),
        "release_ready": status in {"healthy", "warning"} and not errors and bool(baseline.get("baseline_ready", False)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
