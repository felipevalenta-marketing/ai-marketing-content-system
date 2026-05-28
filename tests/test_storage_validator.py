"""Tests for storage record validation."""

from __future__ import annotations

from src.storage.storage_validator import StorageValidator


def test_storage_validator_accepts_token_usage_records():
    validator = StorageValidator()
    record = {
        "record_id": "token_usage_1",
        "record_type": "token_usage",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "instagram_post",
        "campaign_type": "property_launch",
        "execution_id": "exec-1",
        "source_module": "tracking",
        "payload": {
            "provider": "openai",
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        },
        "metadata": {
            "token_usage": {
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
            }
        },
        "warnings": [],
        "errors": [],
    }
    result = validator.validate(record)
    assert result["valid"] is True


def test_storage_validator_flags_sensitive_credentials():
    validator = StorageValidator()
    record = {
        "record_id": "danger",
        "record_type": "generation",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "instagram_post",
        "campaign_type": "property_launch",
        "execution_id": "exec-1",
        "source_module": "pipeline",
        "payload": {"api_key": "sk-test-secret"},
        "metadata": {},
        "warnings": [],
        "errors": [],
    }
    result = validator.validate(record)
    assert result["valid"] is False
    assert any("sensitive" in error.lower() for error in result["errors"])
