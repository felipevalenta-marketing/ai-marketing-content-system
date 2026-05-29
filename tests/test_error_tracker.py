from __future__ import annotations

from src.observability.error_tracker import ErrorTracker


def test_error_tracker_records_and_summarizes_errors() -> None:
    tracker = ErrorTracker(limit=10)
    tracker.record_error(error_type="RuntimeError", module="api", message="boom", request_id="req-1", workflow_id="wf-1", severity="error")
    tracker.record_error(error_type="ValueError", module="workflow", message="bad", request_id="req-2", workflow_id="wf-2", severity="warning")

    recent = tracker.list_recent_errors()
    summary = tracker.summarize_errors()

    assert len(recent) == 2
    assert recent[0]["error_id"]
    assert summary["total_errors"] == 2
    assert summary["by_type"]["RuntimeError"] == 1
    assert summary["by_module"]["workflow"] == 1
