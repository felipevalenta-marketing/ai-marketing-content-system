from __future__ import annotations

from src.api.main import create_app
from src.observability.health_monitor import build_observability_health


def test_health_monitor_returns_safe_sections(auth_services) -> None:
    app = create_app(services={**auth_services})
    health = build_observability_health(app)

    assert health["status"] in {"healthy", "warning", "critical"}
    assert "checks" in health
    assert "timestamp" in health
    assert "storage" in health["sections"]
    assert "metrics" in health["sections"]
    assert "OPENAI_API_KEY" not in str(health)
