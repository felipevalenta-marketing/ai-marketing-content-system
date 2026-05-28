"""Tests for token usage validation."""

from __future__ import annotations

from src.tracking.token_validator import TokenValidator


def test_valid_token_usage_passes(sample_token_usage):
    validator = TokenValidator()
    result = validator.validate(sample_token_usage)

    assert result["valid"] is True
    assert result["errors"] == []


def test_malformed_token_usage_fails():
    validator = TokenValidator()
    result = validator.validate({"provider": "", "input_tokens": -1, "output_tokens": 0, "total_tokens": 0, "estimated": "no", "source": "invalid"})

    assert result["valid"] is False
    assert result["errors"]
