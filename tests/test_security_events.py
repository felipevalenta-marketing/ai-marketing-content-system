from __future__ import annotations

from src.security.security_events import build_security_event, build_security_event_summary, record_security_event


def test_security_event_model_is_sanitized() -> None:
    event = build_security_event(
        event_type="security_warning",
        severity="warning",
        module="security",
        message="Potential issue detected",
        metadata={"token": "Bearer abcdefghijklmnopqrstuvwxyz", "password": "secret"},
    )
    assert event["event_id"]
    assert event["severity"] == "warning"
    assert "Bearer" not in str(event["metadata"])
    assert "secret" not in str(event["metadata"])


def test_security_events_are_recorded_in_memory() -> None:
    record_security_event(event_type="security_warning", severity="warning", module="security", message="Test warning", metadata={"detail": "safe"})
    summary = build_security_event_summary(limit=5)
    assert "recent_events" in summary
    assert summary["total_events"] >= 1
