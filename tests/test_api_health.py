from __future__ import annotations

from fastapi.testclient import TestClient

from src.cli.cli_app import build_parser
from src.api.main import create_app


def test_api_health_and_config_hide_secrets(monkeypatch, auth_services) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")
    app = create_app(services={**auth_services})
    client = TestClient(app)

    health = client.get("/health")
    register = client.post("/auth/register", json={"email": "config@example.com", "password": "Password123", "display_name": "Config User"})
    token = register.json()["data"]["access_token"]
    config = client.get("/config", headers={"Authorization": f"Bearer {token}"})

    assert health.status_code == 200
    assert health.json()["success"] is True
    assert health.json()["data"]["status"] == "ok"
    assert config.status_code == 200
    payload = config.json()
    assert payload["success"] is True
    assert payload["data"]["openai_api_key_present"] is True
    assert "sk-test-secret" not in str(payload)
    assert "OPENAI_API_KEY" not in str(payload)

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "AI Marketing Content System API" in docs.text


def test_api_cli_command_parses() -> None:
    parser = build_parser()
    args = parser.parse_args(["api"])

    assert args.command == "api"
