from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.health import build_health_payload, build_liveness_payload, build_readiness_payload
from src.api.main import create_app


def test_health_endpoints_are_production_friendly(auth_services) -> None:
    app = create_app(services={**auth_services})
    client = TestClient(app)

    health = client.get("/health")
    ready = client.get("/health/ready")
    live = client.get("/health/live")

    assert health.status_code == 200
    assert health.json()["data"]["status"] == "ok"
    assert health.json()["data"]["environment"]
    assert "timestamp" in health.json()["data"]
    assert ready.status_code == 200
    assert live.status_code == 200
    assert ready.json()["data"]["config_loaded"] is True
    assert live.json()["data"]["status"] == "ok"


def test_health_payload_helpers_use_safe_metadata() -> None:
    payload = build_health_payload()
    readiness = build_readiness_payload()
    liveness = build_liveness_payload()

    assert payload["status"] == "ok"
    assert readiness["status"] in {"ok", "warning"}
    assert liveness["status"] == "ok"

