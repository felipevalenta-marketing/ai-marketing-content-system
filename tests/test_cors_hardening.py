from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.api_config import ApiConfig
from src.api.main import create_app


def test_production_cors_blocks_wildcard(monkeypatch, auth_services) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "*,https://app.example.com")
    app = create_app(ApiConfig(), services={**auth_services})
    assert "*" not in app.state.cors_origins
    assert any("wildcard" in warning.lower() for warning in getattr(app.state, "cors_warnings", []))


def test_development_cors_keeps_localhost(monkeypatch, auth_services) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    app = create_app(ApiConfig(), services={**auth_services})
    assert "http://localhost:5173" in app.state.cors_origins


def test_options_preflight_bypasses_rate_limit_and_returns_cors_headers(auth_services) -> None:
    app = create_app(services={**auth_services})
    client = TestClient(app)
    headers = {
        "Origin": "http://127.0.0.1:5173",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,authorization",
    }

    organizations = client.options("/organizations", headers=headers)
    brands = client.options("/brands/wenzel_partner/validate", headers=headers)
    health = client.options("/health", headers=headers)

    assert organizations.status_code == 200
    assert brands.status_code == 200
    assert health.status_code == 200
    assert organizations.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5173"
    assert brands.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5173"
    assert health.headers.get("Access-Control-Allow-Origin") == "http://127.0.0.1:5173"
