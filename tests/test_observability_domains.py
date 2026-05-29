from __future__ import annotations

from src.observability.metrics_registry import get_metrics_registry
from src.observability.workflow_monitor import WorkflowMonitor
from src.tracking.cost_tracker import CostTracker
from src.tracking.token_tracker import TokenTracker


def test_metric_domains_and_observability_metrics_are_grouped() -> None:
    registry = get_metrics_registry()
    registry.reset_metrics()

    token_tracker = TokenTracker()
    cost_tracker = CostTracker()
    token_tracker.track_usage(
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
        },
        metadata={"workflow_id": "workflow-1", "organization_id": "org-1", "brand_id": "brand-1"},
    )
    cost_tracker.track_cost(
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "input_tokens": 10,
            "output_tokens": 5,
            "cached_input_tokens": 0,
            "total_tokens": 15,
            "estimated": False,
        },
        metadata={"workflow_id": "workflow-1", "organization_id": "org-1", "brand_id": "brand-1"},
    )

    token_metrics = registry.get_domain_metrics("tokens")
    cost_metrics = registry.get_domain_metrics("costs")
    workflow_metrics = registry.get_domain_metrics("workflows")

    assert "tokens" in registry.list_domains()
    assert token_metrics["domain"] == "tokens"
    assert token_metrics["metrics"]["total_tokens"] >= 15
    assert token_metrics["metrics"]["by_workflow"]["workflow-1"] >= 15
    assert cost_metrics["domain"] == "costs"
    assert cost_metrics["metrics"]["total_cost"] >= 0
    assert cost_metrics["metrics"]["by_workflow"].get("workflow-1", 0) >= 0
    assert workflow_metrics["domain"] == "workflows"
    assert "total_workflow_runs" in workflow_metrics["metrics"]


def test_workflow_monitor_reports_performance_metrics() -> None:
    monitor = WorkflowMonitor()
    monitor.record_workflow({"workflow_id": "wf-1", "workflow_type": "demo", "status": "success", "duration_seconds": 4.5, "steps": [1, 2]})
    monitor.record_workflow({"workflow_id": "wf-2", "workflow_type": "demo", "status": "failed", "duration_seconds": 1.5, "steps": [1]})

    metrics = monitor.get_metrics()

    assert metrics["total_workflow_runs"] == 2
    assert metrics["completed_workflows"] == 1
    assert metrics["failed_workflows"] == 1
    assert metrics["workflow_success_rate"] == 50.0
    assert metrics["workflow_failure_rate"] == 50.0
    assert metrics["max_workflow_duration"] == 4.5
