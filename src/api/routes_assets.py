"""Asset coordination endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, AssetRequest
from src.auth.current_user import get_current_user_result
from src.assets.asset_coordinator import AssetCoordinator


router = APIRouter(tags=["assets"])


@router.post("/assets", summary="Coordinate assets", description="Use the existing asset coordinator to build an asset plan.", request_model=AssetRequest, response_model=ApiResponse)
def coordinate_assets(request: Request, payload: AssetRequest) -> dict[str, Any]:
    auth_result = get_current_user_result(request)
    if not auth_result.get("success"):
        return build_api_response(success=False, data=None, warnings=auth_result.get("warnings", []), errors=auth_result.get("errors", []), metadata={"route": "assets"}), 401
    coordinator = get_service(request, "assets")
    if coordinator is None:
        coordinator = AssetCoordinator()
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = coordinator.coordinate(request_payload)
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "assets"})
