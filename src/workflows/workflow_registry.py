"""Workflow registry helpers."""

from __future__ import annotations

from typing import Any

from src.workflows.workflow_templates import build_workflow_templates, get_workflow_template_definition


def get_workflow_template(workflow_type: str) -> dict[str, Any]:
    return get_workflow_template_definition(workflow_type)


def list_workflow_templates() -> list[str]:
    return list(build_workflow_templates().keys())


def is_supported_workflow_type(workflow_type: str) -> bool:
    return bool(str(workflow_type).strip()) and str(workflow_type).strip() in build_workflow_templates()

