from __future__ import annotations

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
