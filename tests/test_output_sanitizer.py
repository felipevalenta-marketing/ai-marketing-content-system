from __future__ import annotations

from src.security.output_sanitizer import sanitize_output


def test_output_sanitizer_redacts_sensitive_fields_but_keeps_auth_tokens() -> None:
    payload = {
        "password_hash": "hashed",
        "access_token": "jwt-token",
        "token_type": "bearer",
        "nested": {"api_key": "secret", "token_usage": {"total_tokens": 10}},
    }
    sanitized = sanitize_output(payload)
    assert sanitized["password_hash"] == "[redacted]"
    assert sanitized["access_token"] == "jwt-token"
    assert sanitized["token_type"] == "bearer"
    assert sanitized["nested"]["api_key"] == "[redacted]"
    assert sanitized["nested"]["token_usage"]["total_tokens"] == 10

