from __future__ import annotations

import src.configuration.config_manager as config_manager_module
import src.observability.observability_health as observability_health_module
import src.security.security_health as security_health_module

from src.release.release_health import build_release_health


def test_release_health_returns_safe_summary(monkeypatch) -> None:
    monkeypatch.setattr(config_manager_module.ConfigManager, "validate_configuration", lambda self: {"valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(config_manager_module.ConfigManager, "get_configuration_health", lambda self: {"valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(observability_health_module, "build_observability_health", lambda app=None: {"health_status": "healthy", "health_score": 95, "warnings": [], "errors": []})
    monkeypatch.setattr(security_health_module, "build_security_health", lambda app=None: {"security_status": "healthy", "security_score": 97, "warnings": [], "errors": []})

    result = build_release_health()

    assert result["overall_health"] in {"healthy", "warning", "critical"}
    assert 0 <= result["health_score"] <= 100
    assert "platform_health" in result
    assert "organization_health" in result
