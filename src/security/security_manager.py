"""Security manager orchestration."""

from __future__ import annotations

from typing import Any

from src.security.dependency_validator import validate_dependencies
from src.security.secret_scanner import build_findings_report, scan_repository
from src.security.security_events import build_security_event_summary
from src.security.security_health import build_security_baseline, build_security_health, get_system_status_summary
from src.security.security_result import build_dependency_result, build_success_result
from src.security.security_validator import validate_security


class SecurityManager:
    def __init__(self, config_manager: Any | None = None, logger: Any | None = None) -> None:
        self.config_manager = config_manager
        self.logger = logger

    def validate_security(self, app: Any | None = None) -> dict[str, Any]:
        return validate_security(app or getattr(self, "app", None))

    def calculate_security_score(self, app: Any | None = None) -> int:
        return int(self.get_security_status(app=app).get("security_score", 0))

    def get_security_status(self, app: Any | None = None) -> dict[str, Any]:
        return build_security_health(app or getattr(self, "app", None))

    def build_security_summary(self, app: Any | None = None) -> dict[str, Any]:
        validation = self.validate_security(app=app)
        health = self.get_security_status(app=app)
        dependencies = validate_dependencies()
        findings = build_findings_report()
        summary = {
            "security_score": health.get("security_score", 0),
            "security_status": health.get("security_status", "critical"),
            "baseline_ready": bool(health.get("baseline_ready", False)),
            "baseline_score": int(health.get("baseline_score", 0)),
            "baseline_status": health.get("baseline_status", "critical"),
            "security_ready": bool(health.get("security_ready", False)),
            "release_ready": bool(health.get("release_ready", False)),
            "active_protections": self._active_protections(app=app),
            "findings": findings.get("security_findings", []),
            "findings_count": findings.get("count", 0),
            "dependency_report": dependencies,
            "secret_scan_report": scan_repository(),
            "security_policy": build_security_baseline(app=app).get("policy", {}),
            "security_events": build_security_event_summary(limit=10),
            "warnings": list(health.get("warnings", [])) + list(validation.get("warnings", [])),
            "errors": list(health.get("errors", [])) + list(validation.get("errors", [])),
            "metadata": {
                "system_status": get_system_status_summary(app or getattr(self, "app", None)),
            },
        }
        return summary

    def generate_security_report(self, app: Any | None = None) -> dict[str, Any]:
        summary = self.build_security_summary(app=app)
        health = self.get_security_status(app=app)
        return build_success_result(data={"summary": summary, "health": health}, metadata={"report_type": "security"})

    def get_security_report(self, app: Any | None = None) -> dict[str, Any]:
        return self.generate_security_report(app=app)

    def build_dependency_report(self) -> dict[str, Any]:
        return build_dependency_result(dependencies_valid=bool(validate_dependencies().get("dependencies_valid", False)), metadata={"source": "security_manager"})

    def _active_protections(self, app: Any | None = None) -> dict[str, Any]:
        from src.security.security_config import build_security_configuration

        config = build_security_configuration(app or getattr(self, "app", None))
        return {
            "security_headers": bool(config.get("security_headers_enabled", True)),
            "rate_limiting": bool(config.get("rate_limiting_enabled", True)),
            "secret_scanning": bool(config.get("secret_scanning_enabled", True)),
            "dependency_validation": bool(config.get("dependency_validation_enabled", True)),
            "input_sanitization": bool(config.get("input_sanitization_enabled", True)),
            "output_sanitization": bool(config.get("output_sanitization_enabled", True)),
        }
