"""Tests for token estimation."""

from __future__ import annotations

from src.tracking.token_estimator import TokenEstimator


def test_estimate_text_tokens_uses_character_fallback(monkeypatch):
    estimator = TokenEstimator()
    monkeypatch.setattr("src.tracking.token_estimator.tiktoken", None)

    estimated = estimator.estimate_text_tokens("abcd" * 25, model="unknown-model")

    assert estimated >= 25


def test_estimate_usage_marks_record_as_estimated(monkeypatch):
    estimator = TokenEstimator()
    monkeypatch.setattr("src.tracking.token_estimator.tiktoken", None)

    result = estimator.estimate_usage(
        input_text="Write a premium Mallorca caption.",
        output_text="Discover a calm home near the coast.",
        provider="openai",
        model="gpt-4o-mini",
        metadata={"brand": "wenzel_partner"},
    )

    assert result["estimated"] is True
    assert result["source"] == "estimator"
    assert result["input_tokens"] > 0
    assert result["total_tokens"] == result["input_tokens"] + result["output_tokens"]
