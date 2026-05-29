from __future__ import annotations

from src.api.main import create_app
from src.observability.observability_health import build_observability_configuration, build_observability_health, get_system_status_summary


def test_observability_health_and_system_status_are_safe(auth_services) -> None:
    app = create_app(services={**auth_services})

    health = build_observability_health(app)
    status = get_system_status_summary(app)
    configuration = build_observability_configuration(app)

    assert health["health_score"] >= 0
    assert health["health_status"] in {"healthy", "warning", "critical"}
    assert health["system_status"]["observability"] in {"healthy", "warning", "critical"}
    assert set(status).issuperset({"api", "storage", "auth", "rbac", "brands", "organizations", "workflows", "analytics", "configuration", "observability"})
    assert configuration["observability_enabled"] is True
    assert configuration["request_logging_enabled"] is True
    assert configuration["workflow_monitoring_enabled"] is True
    assert "OPENAI_API_KEY" not in str(health)
