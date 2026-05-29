"""Workflow validation helpers."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
import json
from pathlib import Path

from src.workflows.workflow_registry import get_workflow_template, is_supported_workflow_type


def validate_workflow_plan(plan: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    workflow_type = str(plan.get("workflow_type", "")).strip()
    if not workflow_type:
        errors.append("Missing workflow_type.")
    if workflow_type and not is_supported_workflow_type(workflow_type):
        errors.append(f"Unsupported workflow type: {workflow_type}")
    template = get_workflow_template(workflow_type) if workflow_type else {}
    required_inputs = list(template.get("required_inputs", []))
    metadata = dict(plan.get("metadata", {})) if isinstance(plan.get("metadata"), dict) else {}
    request = dict(plan.get("request", {})) or dict(metadata.get("request", {}))
    for field_name in required_inputs:
        if not str(request.get(field_name, "")).strip() and not request.get(field_name):
            errors.append(f"Missing required workflow input: {field_name}")
    steps = list(plan.get("steps", []))
    step_ids = {str(step.get("step_id", "")) for step in steps}
    for step in steps:
        for dependency in step.get("depends_on", []):
            if dependency not in step_ids:
                errors.append(f"Step dependency not found: {dependency}")
    graph = defaultdict(list)
    for step in steps:
        step_id = str(step.get("step_id", ""))
        for dependency in step.get("depends_on", []):
            graph[dependency].append(step_id)
    if _has_cycle(steps):
        errors.append("Circular dependency detected in workflow plan.")
    approval_gates = plan.get("approval_gates", [])
    if not isinstance(approval_gates, list):
        errors.append("approval_gates must be a list.")
    try:
        json.dumps(plan, default=str)
    except Exception as exc:
        errors.append(f"Workflow plan is not serializable: {exc}")
    storage_root = str(request.get("storage_root", "data"))
    if storage_root and Path(storage_root).is_absolute():
        warnings.append("Workflow storage_root is absolute; ensure StorageManager sanitizes writes.")
    return {"valid": not errors, "warnings": warnings, "errors": errors}


def _has_cycle(steps: list[dict[str, Any]]) -> bool:
    graph = {str(step.get("step_id", "")): list(step.get("depends_on", [])) for step in steps}
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visited:
            return False
        if node in visiting:
            return True
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep in graph and visit(dep):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)
