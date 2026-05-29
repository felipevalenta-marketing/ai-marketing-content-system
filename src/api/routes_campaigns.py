"""Campaign composition endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, CampaignRequest
from src.auth.current_user import get_current_user_result
from src.campaigns.campaign_composer import CampaignComposer


router = APIRouter(tags=["campaigns"])


@router.post("/campaign", summary="Compose a campaign", description="Use the existing campaign composer to build a campaign structure.", request_model=CampaignRequest, response_model=ApiResponse)
def compose_campaign(request: Request, payload: CampaignRequest) -> dict[str, Any]:
    auth_result = get_current_user_result(request)
    if not auth_result.get("success"):
        return build_api_response(success=False, data=None, warnings=auth_result.get("warnings", []), errors=auth_result.get("errors", []), metadata={"route": "campaign"}), 401
    composer = get_service(request, "campaign")
    if composer is None:
        composer = CampaignComposer()
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = composer.compose(request_payload, assets=list(payload.assets))
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "campaign"})
