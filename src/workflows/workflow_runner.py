"""Workflow execution runner."""

from __future__ import annotations

from typing import Any
from copy import deepcopy

from src.workflows.workflow_state import append_error, append_warning, create_initial_state, get_step_output, update_state
from src.workflows.workflow_result import build_step_result


class WorkflowRunner:
    """Execute workflow plans step by step."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    def run(self, plan: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        state = create_initial_state(request, plan)
        if bool(request.get("dry_run")):
            return self.engine.build_result(
                workflow_id=plan.get("workflow_id", ""),
                workflow_type=plan.get("workflow_type", ""),
                status="dry_run",
                steps=[build_step_result(step, {"status": "planned", "warnings": [], "errors": []}) for step in plan.get("steps", [])],
                results={},
                summary={"mode": "dry_run", "planned_steps": len(plan.get("steps", []))},
                warnings=state.get("warnings", []),
                errors=state.get("errors", []),
                metadata={"dry_run": True, "plan": plan},
            )

        step_results: list[dict[str, Any]] = []
        for step in plan.get("steps", []):
            if self.should_skip_step(step, state):
                skipped = {"status": "skipped", "warnings": [], "errors": [], "metadata": {"skipped": True}}
                state = update_state(state, step, skipped)
                step_results.append(build_step_result(step, skipped))
                continue
            try:
                result = self.execute_step(step, state)
            except Exception as exc:  # pragma: no cover - defensive fallback
                result = self.handle_step_failure(step, {"error": str(exc)}, state)
            state = update_state(state, step, result)
            step_results.append(build_step_result(step, result))
            if result.get("status") == "failed" and self.engine.config.workflow_stop_on_critical_failure:
                break

        aggregated = self.engine.aggregate_results(step_results)
        return self.engine.build_result(
            workflow_id=plan.get("workflow_id", ""),
            workflow_type=plan.get("workflow_type", ""),
            status=aggregated.get("status", "completed"),
            steps=step_results,
            results=deepcopy(state.get("step_outputs", {})),
            summary=aggregated.get("summary", {}),
            token_summary=aggregated.get("token_summary", {}),
            cost_summary=aggregated.get("cost_summary", {}),
            report_summary=aggregated.get("report_summary", {}),
            markdown_report=aggregated.get("markdown_report", {}),
            markdown_report_path=aggregated.get("markdown_report_path", ""),
            markdown_sections=aggregated.get("markdown_sections", []),
            markdown_validation=aggregated.get("markdown_validation", {}),
            rendered_markdown=aggregated.get("rendered_markdown", ""),
            rendered_text=aggregated.get("rendered_text", ""),
            storage_summary=aggregated.get("storage_summary", {}),
            warnings=list(dict.fromkeys(state.get("warnings", []) + aggregated.get("warnings", []))),
            errors=list(dict.fromkeys(state.get("errors", []) + aggregated.get("errors", []))),
            metadata={"state": state, "plan": plan},
        )

    def execute_step(self, step: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        return self.engine.run_step(step, state)

    def should_skip_step(self, step: dict[str, Any], state: dict[str, Any]) -> bool:
        if not bool(step.get("enabled", True)):
            return True
        for dependency in step.get("depends_on", []):
            dep_status = state.get("step_statuses", {}).get(dependency)
            if dep_status in {"failed", "skipped"}:
                return True
        return False

    def handle_step_failure(self, step: dict[str, Any], error: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        warning = f"Workflow step failed: {step.get('step_type', '')}"
        state = append_warning(state, warning)
        state = append_error(state, str(error.get("error", "Unknown workflow step failure.")))
        return {
            "status": "failed",
            "warnings": [warning],
            "errors": [str(error.get("error", "Unknown workflow step failure."))],
            "metadata": {"step": step.get("step_type", ""), "error": error},
        }

    def build_step_result(self, step: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        return build_step_result(step, result)
