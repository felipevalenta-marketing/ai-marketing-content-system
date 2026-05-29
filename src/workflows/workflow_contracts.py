"""Workflow contract helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SUPPORTED_WORKFLOW_STATUSES = (
    "planned",
    "running",
    "completed",
    "completed_with_warnings",
    "failed",
    "skipped",
    "requires_approval",
    "dry_run",
)


def build_workflow_request_contract() -> dict[str, Any]:
    return {
        "workflow_type": "",
        "brand": "",
        "platform": "",
        "platforms": [],
        "content_type": "",
        "campaign_type": "",
        "objective": "",
        "audience": "",
        "location": "",
        "property_type": "",
        "visual_style": "",
        "creative_direction": "",
        "assets": [],
        "enable_governance": True,
        "enable_reporting": True,
        "enable_tracking": True,
        "enable_persistence": True,
        "dry_run": False,
        "extra_notes": "",
    }


def build_workflow_step_contract() -> dict[str, Any]:
    return {
        "step_id": "",
        "step_type": "",
        "name": "",
        "description": "",
        "required": True,
        "depends_on": [],
        "enabled": True,
        "status": "planned",
        "input_keys": [],
        "output_keys": [],
        "metadata": {},
    }


def build_workflow_plan_contract() -> dict[str, Any]:
    return {
        "workflow_id": "",
        "workflow_type": "",
        "steps": [],
        "required_inputs": [],
        "optional_inputs": [],
        "approval_gates": [],
        "metadata": {},
        "warnings": [],
        "errors": [],
    }


def build_workflow_state_contract() -> dict[str, Any]:
    return {
        "workflow_id": "",
        "workflow_type": "",
        "request": {},
        "step_outputs": {},
        "step_statuses": {},
        "warnings": [],
        "errors": [],
        "metadata": {},
    }


def build_workflow_result_contract() -> dict[str, Any]:
    return {
        "success": True,
        "workflow_id": "",
        "workflow_type": "",
        "status": "planned",
        "started_at": "",
        "completed_at": "",
        "duration_seconds": 0.0,
        "steps": [],
        "results": {},
        "summary": {},
        "token_summary": {},
        "cost_summary": {},
        "report_summary": {},
        "storage_summary": {},
        "warnings": [],
        "errors": [],
        "metadata": {},
    }


def build_approval_gate_contract() -> dict[str, Any]:
    return {
        "gate_id": "",
        "name": "",
        "description": "",
        "required": True,
        "trigger_steps": [],
        "approval_status": "pending",
        "metadata": {},
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
