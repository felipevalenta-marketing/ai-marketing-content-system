"""Team API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, TeamRequest, TeamUpdateRequest
from src.rbac.rbac_dependencies import authorize_request
from src.rbac.rbac_manager import RBACManager
from src.users.user_manager import UserManager


router = APIRouter(tags=["teams"])


def _rbac(request: Request) -> RBACManager:
    rbac = get_service(request, "rbac")
    if rbac is not None:
        return rbac
    return RBACManager(UserManager())


def _organizations(request: Request):
    organization_manager = get_service(request, "organizations")
    if organization_manager is not None:
        return organization_manager
    from src.organizations.organization_manager import OrganizationManager

    return OrganizationManager()


def _teams(request: Request):
    team_manager = get_service(request, "teams")
    if team_manager is not None:
        return team_manager
    return _organizations(request).membership_manager.team_manager


def _ensure_org_access(request: Request, user: dict[str, Any], organization_id: str) -> dict[str, Any] | None:
    organization_manager = _organizations(request)
    rbac = _rbac(request)
    if rbac.has_any_permission(user, ["admin:all", "organization:manage_members"]):
        return None
    if not organization_manager.can_user_access_organization(str(user.get("user_id", "")), organization_id):
        return build_api_response(success=False, data=None, errors=["Organization access is forbidden."], metadata={"route": "teams", "organization_id": organization_id})
    return None


def _ensure_team_org_access(request: Request, user: dict[str, Any], organization_id: str) -> dict[str, Any] | None:
    organization_manager = _organizations(request)
    if organization_manager.can_user_access_organization(str(user.get("user_id", "")), organization_id):
        return None
    rbac = _rbac(request)
    if rbac.has_any_permission(user, ["admin:all", "organization:manage_members"]):
        return None
    return build_api_response(success=False, data=None, errors=["Organization access is forbidden."], metadata={"route": "teams", "organization_id": organization_id})


@router.get("/organizations/{organization_id}/teams", summary="List teams", description="List teams within an organization.", response_model=ApiResponse)
def list_teams(request: Request, organization_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "team:read")
    if denial is not None:
        return denial
    org_denial = _ensure_org_access(request, user, organization_id)
    if org_denial is not None:
        return org_denial
    teams = _teams(request)
    result = teams.list_teams(organization_id)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "teams.list", "organization_id": organization_id})


@router.post("/organizations/{organization_id}/teams", summary="Create team", description="Create a team within an organization.", request_model=TeamRequest, response_model=ApiResponse)
def create_team(request: Request, organization_id: str, payload: TeamRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "team:create")
    if denial is not None:
        return denial
    org_denial = _ensure_org_access(request, user, organization_id)
    if org_denial is not None:
        return org_denial
    teams = _teams(request)
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = teams.create_team(organization_id, request_payload, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "teams.create", "organization_id": organization_id})


@router.get("/teams/{team_id}", summary="Get team", description="Get a team by id.", response_model=ApiResponse)
def get_team(request: Request, team_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "team:read")
    if denial is not None:
        return denial
    teams = _teams(request)
    team = teams.get_team(team_id)
    if not team:
        return build_api_response(success=False, data=None, errors=["Team not found."], metadata={"route": "teams.get", "team_id": team_id})
    org_denial = _ensure_team_org_access(request, user, str(team.get("organization_id", "")))
    if org_denial is not None:
        return org_denial
    return build_api_response(success=True, data=team, metadata={"route": "teams.get", "team_id": team_id})


@router.patch("/teams/{team_id}", summary="Update team", description="Update a team.", request_model=TeamUpdateRequest, response_model=ApiResponse)
def update_team(request: Request, team_id: str, payload: TeamUpdateRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "team:update")
    if denial is not None:
        return denial
    teams = _teams(request)
    team = teams.get_team(team_id)
    if not team:
        return build_api_response(success=False, data=None, errors=["Team not found."], metadata={"route": "teams.update", "team_id": team_id})
    org_denial = _ensure_team_org_access(request, user, str(team.get("organization_id", "")))
    if org_denial is not None:
        return org_denial
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = teams.update_team(team_id, request_payload, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "teams.update", "team_id": team_id})


def delete_team(request: Request, team_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "team:delete")
    if denial is not None:
        return denial
    teams = _teams(request)
    team = teams.get_team(team_id)
    if not team:
        return build_api_response(success=False, data=None, errors=["Team not found."], metadata={"route": "teams.delete", "team_id": team_id})
    org_denial = _ensure_team_org_access(request, user, str(team.get("organization_id", "")))
    if org_denial is not None:
        return org_denial
    result = teams.archive_team(team_id, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "teams.delete", "team_id": team_id})


router.add_api_route(
    "/teams/{team_id}",
    delete_team,
    methods=["DELETE"],
    summary="Archive team",
    description="Archive a team.",
    response_model=ApiResponse,
)
