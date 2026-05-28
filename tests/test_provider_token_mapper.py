"""Tests for provider token normalization."""

from __future__ import annotations

from src.tracking.provider_token_mapper import ProviderTokenMapper


def test_openai_responses_usage_normalizes_aliases():
    mapper = ProviderTokenMapper()
    result = mapper.normalize(
        "openai",
        {
            "prompt_tokens": 11,
            "completion_tokens": 7,
            "total_tokens": 18,
        },
        model="gpt-4o-mini",
        metadata={"brand": "wenzel_partner"},
        execution_id="exec-1",
    )

    assert result["success"] is True
    assert result["provider"] == "openai"
    assert result["input_tokens"] == 11
    assert result["output_tokens"] == 7
    assert result["total_tokens"] == 18
    assert result["estimated"] is False
    assert result["source"] == "provider_usage"


def test_missing_usage_returns_unavailable_result():
    mapper = ProviderTokenMapper()
    result = mapper.normalize("openai", None, model="gpt-4o-mini")

    assert result["source"] == "unavailable"
    assert result["estimated"] is False
    assert result["total_tokens"] == 0
