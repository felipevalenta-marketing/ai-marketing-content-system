"""Configuration endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_config import build_api_config_summary
from src.api.api_result import build_api_response
from src.rbac.rbac_dependencies import authorize_request
from src.api.schemas import ApiResponse


router = APIRouter(tags=["config"])


@router.get("/config", summary="Get safe configuration summary", description="Return a safe summary of the active configuration without revealing secrets.", response_model=ApiResponse)
def get_config(request: Request) -> dict[str, Any]:
    from src.pipeline.pipeline_config import PipelineConfig

    if PipelineConfig().enable_authentication:
        user, denial = authorize_request(request, "system:read")
        if denial is not None:
            return denial
    return build_api_response(success=True, data=build_api_config_summary(), metadata={"route": "config"})
