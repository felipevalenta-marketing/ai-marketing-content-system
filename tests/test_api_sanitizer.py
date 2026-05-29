from __future__ import annotations

from src.api.sanitizer import sanitize_api_payload


def test_api_sanitizer_redacts_secrets_and_raw_payloads() -> None:
    payload = {
        "api_key": "sk-test-secret",
        "provider_response": {"content": "raw"},
        "token_usage": {"input_tokens": 10, "output_tokens": 5},
        "markdown": "# Safe markdown",
        "storage_path": "C:/Users/FELIPE/secret/file.json",
    }

    sanitized = sanitize_api_payload(payload)

    assert sanitized["api_key"] == "[redacted]"
    assert sanitized["provider_response"] == "[redacted]"
    assert sanitized["token_usage"]["input_tokens"] == 10
    assert sanitized["markdown"] == "# Safe markdown"
    assert sanitized["storage_path"] == "file.json"
