"""Tests for the centralized token tracker."""

from __future__ import annotations

from src.tracking.token_tracker import TokenTracker


def test_track_usage_prefers_provider_usage(sample_token_usage):
    tracker = TokenTracker()
    result = tracker.track_usage(sample_token_usage, metadata={"brand": "wenzel_partner"})

    assert result["source"] == "provider_usage"
    assert result["estimated"] is False
    assert result["total_tokens"] == 200


def test_record_estimated_usage_falls_back_to_estimator():
    tracker = TokenTracker()
    result = tracker.record_estimated_usage(
        "Write a premium Mallorca caption.",
        "Discover a calm home near the coast.",
        metadata={"provider": "openai", "model": "gpt-4o-mini"},
    )

    assert result["estimated"] is True
    assert result["source"] == "estimator"
    assert result["total_tokens"] > 0


def test_aggregate_execution_returns_summary(sample_token_usage):
    tracker = TokenTracker()
    summary = tracker.aggregate_execution([sample_token_usage])

    assert summary["success"] is True
    assert summary["summary"]["exec-1"]["total_tokens"] == 200


def test_get_total_usage_returns_totals(sample_token_usage):
    tracker = TokenTracker()
    summary = tracker.get_total_usage([sample_token_usage])

    assert summary["total_tokens"] == 200
    assert summary["total_input_tokens"] == 120
