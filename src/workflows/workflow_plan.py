"""Workflow plan builder."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.utils.file_utils import normalize_key
from src.workflows.workflow_contracts import build_workflow_plan_contract
from src.workflows.workflow_registry import get_workflow_template, is_supported_workflow_type
from src.workflows.workflow_steps import get_step_definition


def build_workflow_plan(request: dict[str, Any], default_workflow_type: str = "single_content_generation") -> dict[str, Any]:
    workflow_type = normalize_key(str(request.get("workflow_type", "") or default_workflow_type))
    template = get_workflow_template(workflow_type) if is_supported_workflow_type(workflow_type) else {}
    workflow_id = _build_workflow_id(workflow_type, request)
    plan = build_workflow_plan_contract()
    plan.update(
        {
            "workflow_id": workflow_id,
            "workflow_type": workflow_type,
            "steps": _build_steps(template.get("steps", [])),
            "required_inputs": list(template.get("required_inputs", [])),
            "optional_inputs": list(template.get("optional_inputs", [])),
            "approval_gates": _build_approval_gates(template.get("approval_gates", [])),
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "request": dict(request),
                "template_name": template.get("name", workflow_type),
                "dry_run": bool(request.get("dry_run")),
            },
            "warnings": [],
            "errors": [],
        }
    )
    if not template:
        plan["errors"].append(f"Unsupported workflow type: {workflow_type}")
    return plan


def _build_workflow_id(workflow_type: str, request: dict[str, Any]) -> str:
    brand = normalize_key(str(request.get("brand", "") or "workflow"))
    suffix = uuid4().hex[:8]
    return f"{brand}-{workflow_type}-{suffix}"


def _build_steps(step_types: list[str]) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    previous_step_id: str | None = None
    step_type_to_id: dict[str, str] = {}
    for index, step_type in enumerate(step_types, start=1):
        definition = get_step_definition(step_type)
        step_id = f"step_{index:02d}_{step_type}"
        depends_on: list[str] = []
        for dependency in definition.get("dependency_rules", []):
            if dependency in step_type_to_id:
                depends_on.append(step_type_to_id[dependency])
        if previous_step_id and previous_step_id not in depends_on:
            depends_on.append(previous_step_id)
        step_type_to_id[step_type] = step_id
        steps.append(
            {
                "step_id": step_id,
                "step_type": step_type,
                "name": definition.get("name", step_type.replace("_", " ").title()),
                "description": definition.get("description", ""),
                "required": True,
                "depends_on": depends_on,
                "enabled": bool(definition.get("default_enabled", True)),
                "status": "planned",
                "input_keys": list(definition.get("required_inputs", [])),
                "output_keys": list(definition.get("expected_outputs", [])),
                "metadata": {"step_index": index},
            }
        )
        previous_step_id = step_id
    return steps


def _build_approval_gates(gates: list[str]) -> list[dict[str, Any]]:
    approval_gates: list[dict[str, Any]] = []
    for index, gate in enumerate(gates, start=1):
        approval_gates.append(
            {
                "gate_id": f"gate_{index:02d}_{gate}",
                "name": gate.replace("_", " ").title(),
                "description": "Structured approval checkpoint.",
                "required": True,
                "trigger_steps": [],
                "approval_status": "pending",
                "metadata": {"gate_type": gate},
            }
        )
    return approval_gates
