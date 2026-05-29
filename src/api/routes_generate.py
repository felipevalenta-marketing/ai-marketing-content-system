"""Generate endpoint."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, GenerateRequest
from src.rbac.rbac_dependencies import authorize_request
from src.pipeline.pipeline_config import PipelineConfig


router = APIRouter(tags=["generate"])


@router.post("/generate", summary="Run content generation", description="Run the existing content generation pipeline.", request_model=GenerateRequest, response_model=ApiResponse)
def generate_content(request: Request, payload: GenerateRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "generation:create")
    if denial is not None:
        return denial
    pipeline = get_service(request, "pipeline")
    if pipeline is None:
        return build_api_response(success=False, data=None, errors=["Pipeline service is unavailable."], metadata={"route": "generate"})

    config: PipelineConfig = getattr(pipeline, "config", PipelineConfig())
    pipeline.config = replace(
        config,
        enable_persistence=bool(payload.persist),
        enable_reporting=bool(payload.report or payload.markdown),
        enable_markdown_reports=bool(payload.markdown or payload.report),
        enable_markdown_report_export=bool(payload.markdown or payload.report),
        enable_export=bool(payload.persist or payload.report),
    )
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = pipeline.generate(request_payload)
    return build_api_response(
        success=bool(result.get("success", False)),
        data=result,
        warnings=result.get("warnings", []),
        errors=[str(result.get("error"))] if result.get("error") else result.get("errors", []),
        metadata={"route": "generate"},
    )
