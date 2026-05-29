from __future__ import annotations

from src.security.security_policy import build_security_policy, resolve_cors_origins


def test_security_policy_builds_summary(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    policy = build_security_policy()
    assert policy["policy_name"] == "mvp_security_baseline"
    assert "required_checks" in policy
    assert "cors" in policy
    assert policy["cors"]["production"] is False


def test_security_policy_blocks_production_wildcard(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", "*,https://app.example.com")
    policy = build_security_policy()
    assert policy["cors"]["production"] is True
    assert "*" not in policy["cors"]["allow_origins"]
    assert any("wildcard" in warning.lower() for warning in policy["warnings"])


def test_resolve_cors_origins_respects_development_localhost(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173")
    cors = resolve_cors_origins()
    assert cors["allow_origins"] == ["http://localhost:5173"]
