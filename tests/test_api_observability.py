from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app


def _admin_client(auth_services) -> tuple[TestClient, str]:
    app = create_app(services={**auth_services})
    client = TestClient(app)
    register = client.post("/auth/register", json={"email": "observability@example.com", "password": "Password123", "display_name": "Observer"})
    token = register.json()["data"]["access_token"]
    assert register.json()["data"]["user"]["role"] == "admin"
    return client, token


def test_api_observability_endpoints_require_auth_and_return_safe_payload(auth_services) -> None:
    client, token = _admin_client(auth_services)
    headers = {"Authorization": f"Bearer {token}"}

    unauthorized = client.get("/observability/metrics")
    assert unauthorized.status_code == 401

    health = client.get("/observability/health", headers=headers)
    status = client.get("/observability/status", headers=headers)
    domains = client.get("/observability/domains", headers=headers)
    tokens = client.get("/observability/tokens", headers=headers)
    costs = client.get("/observability/costs", headers=headers)
    configuration = client.get("/observability/configuration", headers=headers)
    metrics = client.get("/observability/metrics", headers=headers)
    runtime = client.get("/observability/runtime", headers=headers)
    errors = client.get("/observability/errors", headers=headers)
    workflows = client.get("/observability/workflows", headers=headers)
    storage = client.get("/observability/storage", headers=headers)

    assert health.status_code == 200
    assert status.status_code == 200
    assert domains.status_code == 200
    assert tokens.status_code == 200
    assert costs.status_code == 200
    assert configuration.status_code == 200
    assert metrics.status_code == 200
    assert runtime.status_code == 200
    assert errors.status_code == 200
    assert workflows.status_code == 200
    assert storage.status_code == 200

    payload = health.json()["data"]
    assert payload["status"] in {"healthy", "warning", "critical"}
    assert "checks" in payload
    assert "observability" in status.json()["data"]
    assert len(domains.json()["data"]["domains"]) >= 1
    assert "total_tokens" in tokens.json()["data"]
    assert "total_cost" in costs.json()["data"]
    assert "observability_enabled" in configuration.json()["data"]
    assert "OPENAI_API_KEY" not in str(payload)
    assert "domain" in str(domains.json()).lower()
    assert "sk-" not in str(metrics.json())
    assert "password" not in str(errors.json()).lower()
    assert "OPENAI_API_KEY" not in str(tokens.json())
    assert "workflow_metrics" in workflows.json()["data"]


def test_public_health_routes_still_work(auth_services) -> None:
    client, _ = _admin_client(auth_services)
    assert client.get("/health").status_code == 200
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
