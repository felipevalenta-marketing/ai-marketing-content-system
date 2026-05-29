"""Tests for workflow state helpers."""

from __future__ import annotations

from src.workflows.workflow_state import append_error, append_warning, create_initial_state, get_step_output, serialize_state, update_state


def test_workflow_state_tracks_step_outputs(sample_workflow_request):
    plan = {"workflow_id": "wf-1", "workflow_type": "full_campaign_package", "steps": [], "warnings": [], "errors": []}
    state = create_initial_state(sample_workflow_request, plan)
    step = {"step_id": "step_01_load_context", "step_type": "load_context"}
    result = {"status": "completed", "context": {"loaded": True}}

    updated = update_state(state, step, result)

    assert get_step_output(updated, "step_01_load_context")["context"]["loaded"] is True
    assert updated["step_statuses"]["step_01_load_context"] == "completed"


def test_workflow_state_serialization(sample_workflow_request):
    state = create_initial_state(sample_workflow_request, {"workflow_id": "wf-2", "workflow_type": "single_content_generation"})
    state = append_warning(state, "sample warning")
    state = append_error(state, "sample error")

    serialized = serialize_state(state)

    assert serialized["warnings"] == ["sample warning"]
    assert serialized["errors"] == ["sample error"]
