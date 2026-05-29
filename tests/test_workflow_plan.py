"""Tests for workflow plan building."""

from __future__ import annotations

from src.workflows.workflow_plan import build_workflow_plan


def test_workflow_plan_builds_step_order(sample_workflow_request):
    plan = build_workflow_plan(sample_workflow_request)

    assert plan["workflow_id"]
    assert plan["workflow_type"] == "full_campaign_package"
    assert plan["steps"]
    assert plan["steps"][0]["step_type"] == "load_context"
    assert plan["steps"][-1]["step_type"] == "persist_results"


def test_workflow_plan_uses_step_ids_for_dependencies(sample_workflow_request):
    plan = build_workflow_plan(sample_workflow_request)

    step_ids = {step["step_id"] for step in plan["steps"]}
    for step in plan["steps"]:
        for dependency in step["depends_on"]:
            assert dependency in step_ids
