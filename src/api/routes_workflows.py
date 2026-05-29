"""Workflow orchestration endpoint."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, WorkflowRequest
from src.rbac.rbac_dependencies import authorize_request
from src.rbac.rbac_manager import RBACManager
from src.users.user_manager import UserManager
from src.pipeline.pipeline_config import PipelineConfig
from src.workflows.workflow_engine import WorkflowEngine


router = APIRouter(tags=["workflows"])


def _resolve_org_context(request: Request, user: dict[str, Any], payload: WorkflowRequest) -> tuple[str, str, dict[str, Any] | None]:
    organization_manager = get_service(request, "organizations")
    brand_access = get_service(request, "brand_access")
    rbac = get_service(request, "rbac") or RBACManager(UserManager())
    organization_id = str(payload.organization_id or user.get("active_organization_id") or "").strip()
    team_id = str(payload.team_id or user.get("active_team_id") or "").strip()
    if organization_id and organization_manager and not (rbac.has_any_permission(user, ["admin:all", "organization:manage_members"]) or organization_manager.can_user_access_organization(str(user.get("user_id", "")), organization_id, team_id or None)):
        return organization_id, team_id, build_api_response(success=False, data=None, errors=["Organization access is forbidden."], metadata={"route": "workflow", "organization_id": organization_id, "team_id": team_id})
    if organization_id and payload.brand and brand_access is not None and hasattr(brand_access, "can_access_brand") and not brand_access.can_access_brand(organization_id, payload.brand, "use"):
        return organization_id, team_id, build_api_response(success=False, data=None, errors=["Brand access is forbidden for the selected organization."], metadata={"route": "workflow", "organization_id": organization_id, "brand": payload.brand})
    return organization_id, team_id, None


@router.post("/workflow", summary="Run a workflow", description="Execute the workflow orchestration layer.", request_model=WorkflowRequest, response_model=ApiResponse)
def run_workflow(request: Request, payload: WorkflowRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "workflow:run")
    if denial is not None:
        return denial
    organization_id, team_id, org_denial = _resolve_org_context(request, user, payload)
    if org_denial is not None:
        return org_denial
    workflow_engine = get_service(request, "workflow")
    pipeline = get_service(request, "pipeline")
    if workflow_engine is None:
        if pipeline is None:
            return build_api_response(success=False, data=None, errors=["Workflow service is unavailable."], metadata={"route": "workflow"})
        config: PipelineConfig = getattr(pipeline, "config", PipelineConfig())
        workflow_engine = WorkflowEngine(config=replace(config, enable_persistence=bool(payload.persist)), pipeline=pipeline)
    else:
        workflow_engine.config = replace(
            getattr(workflow_engine, "config", PipelineConfig()),
            enable_persistence=bool(payload.persist),
            workflow_persistence_enabled=bool(payload.persist),
            enable_reporting=bool(payload.report or payload.markdown),
            enable_markdown_reports=bool(payload.markdown or payload.report),
            enable_markdown_report_export=bool(payload.markdown or payload.report),
        )
        workflow_pipeline = getattr(workflow_engine, "pipeline", None)
        if workflow_pipeline is not None and hasattr(workflow_pipeline, "config"):
            workflow_pipeline.config = replace(
                getattr(workflow_pipeline, "config", PipelineConfig()),
                enable_persistence=bool(payload.persist),
                enable_reporting=bool(payload.report or payload.markdown),
                enable_markdown_reports=bool(payload.markdown or payload.report),
                enable_markdown_report_export=bool(payload.markdown or payload.report),
            )

    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    request_payload["workflow_type"] = payload.workflow_type
    request_payload["dry_run"] = bool(payload.dry_run)
    request_payload["organization_id"] = organization_id
    request_payload["team_id"] = team_id
    result = workflow_engine.create_workflow(request_payload)
    return build_api_response(
        success=bool(result.get("success", False)),
        data=result,
        warnings=result.get("warnings", []),
        errors=result.get("errors", []),
        metadata={"route": "workflow"},
    )
