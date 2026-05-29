from __future__ import annotations

from src.observability.log_sanitizer import redact_log_payload


def test_log_sanitizer_redacts_nested_secrets() -> None:
    payload = {
        "message": "OPENAI_API_KEY=sk-secret-value",
        "authorization": "Bearer abcdefgh",
        "metadata": {
            "password": "secret",
            "token_usage": {"total_tokens": 12},
            "cost_usage": {"total_cost": 1.5},
        },
        "path": "C:/Users/FELIPE/secrets.txt",
    }

    sanitized = redact_log_payload(payload)

    assert sanitized["message"] == "[redacted]"
    assert sanitized["authorization"] == "[redacted]"
    assert sanitized["metadata"]["password"] == "[redacted]"
    assert sanitized["metadata"]["token_usage"]["total_tokens"] == 12
    assert sanitized["metadata"]["cost_usage"]["total_cost"] == 1.5
    assert sanitized["path"] == "secrets.txt"
