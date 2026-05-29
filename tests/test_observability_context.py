from __future__ import annotations

from src.observability.observability_context import build_context, clear_context, get_context, sanitize_context


def test_observability_context_sanitizes_sensitive_values() -> None:
    context = build_context(
        request_context={"method": "GET", "path": "/health", "authorization": "Bearer secret-token"},
        user_context={"user_id": "user-1", "email": "test@example.com", "password": "secret"},
        organization_context={"organization_id": "org-1"},
        team_context={"team_id": "team-1"},
        workflow_context={"workflow_id": "workflow-1"},
        metadata={"api_key": "sk-secret"},
    )

    assert context["request"]["authorization"] == "[redacted]"
    assert context["user"]["password"] == "[redacted]"
    assert context["metadata"]["api_key"] == "[redacted]"
    assert get_context()["workflow"]["workflow_id"] == "workflow-1"
    assert "secret-token" not in str(context)
    clear_context()
    assert get_context() == {}


def test_sanitize_context_handles_non_dict() -> None:
    assert sanitize_context(None) == {}
