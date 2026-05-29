"""Workflow execution state helpers."""

from __future__ import annotations

from typing import Any
from copy import deepcopy

from src.workflows.workflow_contracts import build_workflow_state_contract, utc_now


def create_initial_state(request: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    state = build_workflow_state_contract()
    state.update(
        {
            "workflow_id": str(plan.get("workflow_id", "")),
            "workflow_type": str(plan.get("workflow_type", "")),
            "request": deepcopy(request or {}),
            "step_outputs": {},
            "step_statuses": {},
            "warnings": list(plan.get("warnings", [])),
            "errors": list(plan.get("errors", [])),
            "metadata": {
                "created_at": utc_now(),
                "plan": deepcopy(plan),
            },
        }
    )
    return state


def update_state(state: dict[str, Any], step: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    step_id = str(step.get("step_id", step.get("step_type", "")))
    updated = deepcopy(state or {})
    updated.setdefault("step_outputs", {})
    updated.setdefault("step_statuses", {})
    updated.setdefault("warnings", [])
    updated.setdefault("errors", [])
    updated["step_outputs"][step_id] = deepcopy(result)
    updated["step_statuses"][step_id] = str(result.get("status", step.get("status", "completed")))
    updated["metadata"] = deepcopy(updated.get("metadata", {}))
    updated["metadata"]["updated_at"] = utc_now()
    for warning in result.get("warnings", []) or []:
        if warning and warning not in updated["warnings"]:
            updated["warnings"].append(str(warning))
    for error in result.get("errors", []) or []:
        if error and error not in updated["errors"]:
            updated["errors"].append(str(error))
    return updated


def get_step_output(state: dict[str, Any], key: str, default: Any | None = None) -> Any:
    return deepcopy(state.get("step_outputs", {}).get(key, default))


def append_warning(state: dict[str, Any], warning: str) -> dict[str, Any]:
    updated = deepcopy(state or {})
    updated.setdefault("warnings", [])
    if warning and warning not in updated["warnings"]:
        updated["warnings"].append(str(warning))
    return updated


def append_error(state: dict[str, Any], error: str) -> dict[str, Any]:
    updated = deepcopy(state or {})
    updated.setdefault("errors", [])
    if error and error not in updated["errors"]:
        updated["errors"].append(str(error))
    return updated


def serialize_state(state: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(state or {})

