"""Workflow orchestration endpoint."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, WorkflowRequest
from src.pipeline.pipeline_config import PipelineConfig
from src.workflows.workflow_engine import WorkflowEngine


router = APIRouter(tags=["workflows"])


@router.post("/workflow", summary="Run a workflow", description="Execute the workflow orchestration layer.", request_model=WorkflowRequest, response_model=ApiResponse)
def run_workflow(request: Request, payload: WorkflowRequest) -> dict[str, Any]:
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
    result = workflow_engine.create_workflow(request_payload)
    return build_api_response(
        success=bool(result.get("success", False)),
        data=result,
        warnings=result.get("warnings", []),
        errors=result.get("errors", []),
        metadata={"route": "workflow"},
    )
