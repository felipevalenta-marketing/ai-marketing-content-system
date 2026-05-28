"""Tests for token aggregation."""

from __future__ import annotations

from src.tracking.token_aggregator import TokenAggregator


def test_aggregate_by_execution_and_summary(sample_token_usage):
    aggregator = TokenAggregator()
    summary = aggregator.summarize_usage([sample_token_usage, {**sample_token_usage, "execution_id": "exec-2", "total_tokens": 50, "input_tokens": 20, "output_tokens": 30}])

    assert summary["total_input_tokens"] == 140
    assert summary["total_output_tokens"] == 110
    assert summary["total_tokens"] == 250
    assert summary["records_count"] == 2
    assert summary["by_provider"]["summary"]["openai"]["records_count"] == 2


def test_aggregate_by_module_and_campaign(sample_token_usage):
    aggregator = TokenAggregator()
    records = [
        sample_token_usage,
        {**sample_token_usage, "module": "campaign", "campaign_id": "campaign-2", "asset_type": "image_prompt", "input_tokens": 5, "output_tokens": 10, "total_tokens": 15},
    ]

    module_summary = aggregator.aggregate_by_module(records)
    campaign_summary = aggregator.aggregate_by_campaign(records)
    asset_summary = aggregator.aggregate_by_asset(records)

    assert "generation" in module_summary["summary"]
    assert "campaign-2" in campaign_summary["summary"]
    assert "image_prompt" in asset_summary["summary"]
