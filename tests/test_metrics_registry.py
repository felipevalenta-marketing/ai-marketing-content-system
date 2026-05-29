from __future__ import annotations

from src.observability.metrics_registry import get_metrics_registry


def test_metrics_registry_increment_record_and_reset() -> None:
    registry = get_metrics_registry()
    registry.reset_metrics()

    registry.increment_counter("total_requests")
    registry.increment_counter("requests_by_path", labels={"path": "/health"})
    registry.increment_counter("requests_by_status", labels={"status": "200"})
    registry.record_duration("request_duration_ms", 10.0)
    registry.increment_counter("workflow_runs")
    registry.increment_counter("workflow_failures")
    registry.increment_counter("storage_errors")
    registry.increment_counter("token_usage_total", value=123)
    registry.increment_counter("cost_total", value=4.56)
    registry.increment_counter("auth_failures")

    metrics = registry.get_metrics()

    assert metrics["total_requests"] >= 1
    assert metrics["requests_by_path"]["path=/health"] == 1
    assert metrics["requests_by_status"]["status=200"] == 1
    assert metrics["average_response_time_ms"] == 10.0
    assert metrics["workflow_runs"] >= 1
    assert metrics["workflow_failures"] >= 1
    assert metrics["storage_errors"] >= 1
    assert metrics["token_usage_total"] >= 123
    assert metrics["cost_total"] >= 4.56
    assert metrics["auth_failures"] >= 1

    registry.reset_metrics()
    reset = registry.get_metrics()
    assert reset["total_requests"] == 0
