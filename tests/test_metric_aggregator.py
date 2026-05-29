from __future__ import annotations

from src.analytics.metric_aggregator import MetricAggregator


def test_metric_aggregator_summarizes_tokens_and_costs() -> None:
    aggregator = MetricAggregator()
    token_records = [
        {
            "record_type": "token_usage",
            "payload": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "module": "content",
                "campaign_id": "launch",
                "asset_type": "instagram_post",
                "input_tokens": 12,
                "output_tokens": 8,
                "total_tokens": 20,
                "estimated": False,
            },
        },
        {
            "record_type": "token_usage",
            "payload": {
                "provider": "openai",
                "model": "gpt-4o",
                "module": "workflow",
                "campaign_id": "launch",
                "asset_type": "workflow",
                "input_tokens": 5,
                "output_tokens": 5,
                "total_tokens": 10,
                "estimated": True,
            },
        },
    ]
    cost_records = [
        {
            "record_type": "cost_usage",
            "payload": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "currency": "USD",
                "input_cost": 0.01,
                "output_cost": 0.02,
                "cached_input_cost": 0.0,
                "total_cost": 0.03,
                "estimated_cost": False,
                "pricing_found": True,
            },
        }
    ]
    workflow_records = [
        {"record_type": "workflow", "status": "completed", "summary": {"completed_steps": 3, "skipped_steps": 1, "failed_steps": 0}},
        {"record_type": "workflow", "status": "failed", "summary": {"completed_steps": 1, "skipped_steps": 0, "failed_steps": 1}},
    ]

    token_summary = aggregator.aggregate_tokens(token_records)
    cost_summary = aggregator.aggregate_costs(cost_records)
    workflow_summary = aggregator.aggregate_workflows(workflow_records)

    assert token_summary["total_input_tokens"] == 17
    assert token_summary["total_output_tokens"] == 13
    assert token_summary["estimated_records"] == 1
    assert token_summary["by_provider"]["openai"]["total_tokens"] == 30
    assert cost_summary["total_cost"] == 0.03
    assert cost_summary["currency"] == "USD"
    assert cost_summary["unknown_pricing_records"] == 0
    assert workflow_summary["total_workflows"] == 2
    assert workflow_summary["failed_workflows"] == 1
    assert workflow_summary["completed_steps"] == 4

