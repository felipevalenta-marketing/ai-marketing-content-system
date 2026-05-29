"""Tests for workflow validation."""

from __future__ import annotations

from src.workflows.workflow_plan import build_workflow_plan
from src.workflows.workflow_validator import validate_workflow_plan


def test_workflow_validator_accepts_valid_plan(sample_workflow_request):
    plan = build_workflow_plan(sample_workflow_request)
    validation = validate_workflow_plan(plan)

    assert validation["valid"] is True
    assert validation["errors"] == []


def test_workflow_validator_detects_cycle(sample_workflow_request):
    plan = build_workflow_plan(sample_workflow_request)
    step_a = plan["steps"][0]
    step_b = plan["steps"][1]
    step_a["depends_on"] = [step_b["step_id"]]
    step_b["depends_on"] = [step_a["step_id"]]

    validation = validate_workflow_plan(plan)

    assert validation["valid"] is False
    assert any("Circular dependency" in error for error in validation["errors"])
