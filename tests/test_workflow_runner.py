"""Tests for workflow runner behavior."""

from __future__ import annotations

from types import SimpleNamespace

from src.workflows.workflow_runner import WorkflowRunner


class FakeWorkflowEngine:
    def __init__(self) -> None:
        self.config = SimpleNamespace(workflow_stop_on_critical_failure=True)

    def run_step(self, step, state):
        step_type = step["step_type"]
        outputs = {
            "load_context": {"status": "completed", "context": {"loaded": True}},
            "build_prompt": {"status": "completed", "prompt_payload": {"user_prompt": "Prompt"}},
            "generate_content": {"status": "completed", "ai_response": {"success": True, "token_usage": {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 10, "output_tokens": 5, "total_tokens": 15, "estimated": False, "source": "provider_usage", "execution_id": "wf-1", "module": "workflow", "operation": "generate_content", "campaign_id": "campaign-1", "asset_type": "instagram_post"}}},
            "track_tokens": {"status": "completed", "token_usage": {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 10, "output_tokens": 5, "total_tokens": 15, "estimated": False, "source": "provider_usage", "execution_id": "wf-1", "module": "workflow", "operation": "generate_content", "campaign_id": "campaign-1", "asset_type": "instagram_post"}},
            "track_costs": {"status": "completed", "cost_usage": {"provider": "openai", "model": "gpt-4o-mini", "currency": "USD", "input_tokens": 10, "output_tokens": 5, "cached_input_tokens": 0, "total_tokens": 15, "input_cost": 0.0, "output_cost": 0.0, "cached_input_cost": 0.0, "total_cost": 0.0, "estimated_tokens": False, "estimated_cost": True, "pricing_found": False, "pricing_version": "", "pricing_source": "", "execution_id": "wf-1", "module": "workflow", "operation": "generate_content", "campaign_id": "campaign-1", "asset_type": "instagram_post"}},
        }
        if step_type == "fail_step":
            return {"status": "failed", "warnings": [], "errors": ["boom"]}
        return outputs.get(step_type, {"status": "completed", "warnings": [], "errors": []})

    def build_result(self, **kwargs):
        return kwargs

    def aggregate_results(self, step_results):
        status = "completed"
        if any(step.get("status") == "failed" for step in step_results):
            status = "failed"
        return {
            "status": status,
            "summary": {"step_count": len(step_results), "completed_steps": len(step_results), "failed_steps": 0, "skipped_steps": 0, "duration_seconds": 0.0},
            "warnings": [],
            "errors": [],
            "token_summary": {"total_tokens": 15},
            "cost_summary": {"total_cost": 0.0},
            "report_summary": {},
            "storage_summary": {},
        }


def test_workflow_runner_dry_run_skips_execution(sample_workflow_request):
    engine = FakeWorkflowEngine()
    runner = WorkflowRunner(engine)
    plan = {
        "workflow_id": "wf-1",
        "workflow_type": "single_content_generation",
        "steps": [{"step_id": "step_01_load_context", "step_type": "load_context", "name": "Load Context", "enabled": True, "depends_on": []}],
        "warnings": [],
        "errors": [],
    }
    request = dict(sample_workflow_request)
    request["dry_run"] = True

    result = runner.run(plan, request)

    assert result["status"] == "dry_run"
    assert result["summary"]["planned_steps"] == 1


def test_workflow_runner_executes_steps_in_order(sample_workflow_request):
    engine = FakeWorkflowEngine()
    runner = WorkflowRunner(engine)
    plan = {
        "workflow_id": "wf-2",
        "workflow_type": "single_content_generation",
        "steps": [
            {"step_id": "step_01_load_context", "step_type": "load_context", "name": "Load Context", "enabled": True, "depends_on": []},
            {"step_id": "step_02_build_prompt", "step_type": "build_prompt", "name": "Build Prompt", "enabled": True, "depends_on": ["step_01_load_context"]},
        ],
        "warnings": [],
        "errors": [],
    }

    result = runner.run(plan, sample_workflow_request)

    assert result["status"] == "completed"
    assert result["summary"]["step_count"] == 2


def test_workflow_runner_skips_disabled_steps(sample_workflow_request):
    engine = FakeWorkflowEngine()
    runner = WorkflowRunner(engine)
    plan = {
        "workflow_id": "wf-3",
        "workflow_type": "single_content_generation",
        "steps": [
            {"step_id": "step_01_load_context", "step_type": "load_context", "name": "Load Context", "enabled": False, "depends_on": []},
        ],
        "warnings": [],
        "errors": [],
    }

    result = runner.run(plan, sample_workflow_request)

    assert result["status"] == "completed"
    assert result["steps"][0]["status"] == "skipped"


def test_workflow_runner_handles_failures(sample_workflow_request):
    engine = FakeWorkflowEngine()
    runner = WorkflowRunner(engine)
    plan = {
        "workflow_id": "wf-4",
        "workflow_type": "single_content_generation",
        "steps": [
            {"step_id": "step_01_fail_step", "step_type": "fail_step", "name": "Fail Step", "enabled": True, "depends_on": []},
        ],
        "warnings": [],
        "errors": [],
    }

    result = runner.run(plan, sample_workflow_request)

    assert result["status"] == "failed"
    assert result["errors"]
