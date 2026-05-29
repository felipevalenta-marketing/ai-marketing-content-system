"""Workflow result helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.workflows.workflow_contracts import build_workflow_result_contract, utc_now


def build_success_result(**kwargs: Any) -> dict[str, Any]:
    result = build_workflow_result_contract()
    result.update(kwargs)
    result["success"] = True
    return result


def build_failure_result(error: str, **kwargs: Any) -> dict[str, Any]:
    result = build_workflow_result_contract()
    result.update(kwargs)
    result["success"] = False
    result["status"] = kwargs.get("status", "failed")
    result.setdefault("errors", [])
    if error:
        result["errors"] = list(result["errors"]) + [error]
    return result


def build_dry_run_result(**kwargs: Any) -> dict[str, Any]:
    result = build_workflow_result_contract()
    result.update(kwargs)
    result["success"] = True
    result["status"] = "dry_run"
    return result


def build_step_result(step: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": step.get("step_id", ""),
        "step_type": step.get("step_type", ""),
        "name": step.get("name", ""),
        "status": result.get("status", "completed"),
        "warnings": list(result.get("warnings", [])),
        "errors": list(result.get("errors", [])),
        "metadata": deepcopy(result.get("metadata", {})),
        "output_keys": list(result.get("output_keys", [])),
        "result": deepcopy(result),
    }


def build_validation_failure_result(errors: list[str], warnings: list[str], **kwargs: Any) -> dict[str, Any]:
    result = build_workflow_result_contract()
    result.update(kwargs)
    result["success"] = False
    result["status"] = "failed"
    result["errors"] = list(errors)
    result["warnings"] = list(warnings)
    return result


def normalize_workflow_status(status: str | None) -> str:
    value = str(status or "").strip().lower()
    if value in {"planned", "running", "completed", "completed_with_warnings", "failed", "skipped", "requires_approval", "dry_run"}:
        return value
    return "planned"
