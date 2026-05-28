from __future__ import annotations

from src.tracking.cost_aggregator import CostAggregator


def test_cost_aggregator_summarizes_records(sample_cost_usage: dict[str, object]) -> None:
    aggregator = CostAggregator()
    summary = aggregator.summarize_cost([sample_cost_usage, sample_cost_usage])
    assert summary["records_count"] == 2
    assert summary["estimated_cost_records"] == 2
    assert summary["unknown_pricing_records"] == 2
    assert "by_provider" in summary
    assert "by_model" in summary


def test_cost_aggregator_groups_by_execution(sample_cost_usage: dict[str, object]) -> None:
    aggregator = CostAggregator()
    grouped = aggregator.aggregate_by_execution([sample_cost_usage])
    assert grouped["success"] is True
    assert "exec-1" in grouped["summary"]


def test_cost_aggregator_groups_by_provider_and_model(sample_cost_usage: dict[str, object]) -> None:
    aggregator = CostAggregator()
    provider_grouped = aggregator.aggregate_by_provider([sample_cost_usage])
    model_grouped = aggregator.aggregate_by_model([sample_cost_usage])
    assert provider_grouped["success"] is True
    assert model_grouped["success"] is True
    assert "openai" in provider_grouped["summary"]
    assert "gpt-4o-mini" in model_grouped["summary"]
