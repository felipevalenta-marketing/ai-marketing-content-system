"""Asset coordination endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, AssetRequest
from src.rbac.rbac_dependencies import authorize_request
from src.rbac.rbac_manager import RBACManager
from src.users.user_manager import UserManager
from src.assets.asset_coordinator import AssetCoordinator


router = APIRouter(tags=["assets"])


def _resolve_org_context(request: Request, user: dict[str, Any], payload: AssetRequest) -> tuple[str, str, dict[str, Any] | None]:
    organization_manager = get_service(request, "organizations")
    brand_access = get_service(request, "brand_access")
    rbac = get_service(request, "rbac") or RBACManager(UserManager())
    organization_id = str(payload.organization_id or user.get("active_organization_id") or "").strip()
    team_id = str(payload.team_id or user.get("active_team_id") or "").strip()
    if organization_id and organization_manager and not (rbac.has_any_permission(user, ["admin:all", "organization:manage_members"]) or organization_manager.can_user_access_organization(str(user.get("user_id", "")), organization_id, team_id or None)):
        return organization_id, team_id, build_api_response(success=False, data=None, errors=["Organization access is forbidden."], metadata={"route": "assets", "organization_id": organization_id, "team_id": team_id})
    if organization_id and payload.brand and brand_access is not None and hasattr(brand_access, "can_access_brand") and not brand_access.can_access_brand(organization_id, payload.brand, "use"):
        return organization_id, team_id, build_api_response(success=False, data=None, errors=["Brand access is forbidden for the selected organization."], metadata={"route": "assets", "organization_id": organization_id, "brand": payload.brand})
    return organization_id, team_id, None


@router.post("/assets", summary="Coordinate assets", description="Use the existing asset coordinator to build an asset plan.", request_model=AssetRequest, response_model=ApiResponse)
def coordinate_assets(request: Request, payload: AssetRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "asset:create")
    if denial is not None:
        return denial
    organization_id, team_id, org_denial = _resolve_org_context(request, user, payload)
    if org_denial is not None:
        return org_denial
    coordinator = get_service(request, "assets")
    if coordinator is None:
        coordinator = AssetCoordinator()
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    request_payload["organization_id"] = organization_id
    request_payload["team_id"] = team_id
    result = coordinator.coordinate(request_payload)
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "assets"})
