from __future__ import annotations

from src.security.security_health import build_security_baseline, build_security_health, get_system_status_summary
from src.security.security_manager import SecurityManager


def test_security_health_returns_expected_shape() -> None:
    result = build_security_health()
    assert "security_score" in result
    assert "security_status" in result
    assert isinstance(result["warnings"], list)
    assert isinstance(result["recommendations"], list)


def test_security_status_summary_includes_security() -> None:
    result = get_system_status_summary()
    assert "security" in result


def test_security_manager_builds_summary() -> None:
    manager = SecurityManager()
    summary = manager.build_security_summary()
    assert "security_score" in summary
    assert "active_protections" in summary


def test_security_baseline_returns_expected_shape(monkeypatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "x" * 32)
    baseline = build_security_baseline()
    assert "baseline_ready" in baseline
    assert "baseline_score" in baseline
    assert "checks" in baseline
    assert isinstance(baseline["checks"], dict)
