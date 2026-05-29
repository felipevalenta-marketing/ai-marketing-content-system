"""RBAC API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, RoleAssignmentRequest
from src.auth.current_user import get_current_user_result
from src.rbac.rbac_dependencies import authorize_request, authorize_request_any
from src.rbac.rbac_manager import RBACManager
from src.users.user_manager import UserManager


router = APIRouter(tags=["rbac"])


def _get_rbac(request: Request) -> RBACManager:
    rbac = get_service(request, "rbac")
    if rbac is not None:
        return rbac
    users = get_service(request, "users")
    if isinstance(users, UserManager):
        return RBACManager(users)
    return RBACManager(UserManager())


@router.get("/rbac/roles", summary="List roles", description="Return available roles and their permissions.", response_model=ApiResponse)
def get_roles(request: Request) -> dict[str, Any]:
    user, denial = authorize_request_any(request, ["user:read", "system:read"])
    if denial is not None:
        return denial
    rbac = _get_rbac(request)
    result = rbac.list_roles()
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "rbac.roles"})


@router.get("/rbac/permissions", summary="List permissions", description="Return available permissions and their groups.", response_model=ApiResponse)
def get_permissions(request: Request) -> dict[str, Any]:
    user, denial = authorize_request_any(request, ["user:read", "system:read"])
    if denial is not None:
        return denial
    rbac = _get_rbac(request)
    result = rbac.list_permissions()
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "rbac.permissions"})


@router.get("/rbac/health", summary="RBAC health", description="Return RBAC configuration and hierarchy health.", response_model=ApiResponse)
def get_health(request: Request) -> dict[str, Any]:
    user, denial = authorize_request(request, "system:read")
    if denial is not None:
        return denial
    rbac = _get_rbac(request)
    result = rbac.get_health()
    return build_api_response(success=True, data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "rbac.health"})


@router.get("/rbac/me", summary="My access", description="Return the authenticated user's role and permissions.", response_model=ApiResponse)
def get_me(request: Request) -> dict[str, Any]:
    current = get_current_user_result(request)
    if not current.get("success"):
        return build_api_response(success=False, data=None, warnings=current.get("warnings", []), errors=current.get("errors", []), metadata={"route": "rbac.me"}), 401
    user = current.get("user", {}) if isinstance(current.get("user"), dict) else {}
    rbac = _get_rbac(request)
    result = rbac.build_access_summary(user)
    return build_api_response(success=True, data=result, metadata={"route": "rbac.me"})


@router.patch("/users/{user_id}/role", summary="Assign user role", description="Assign a role to a user.", request_model=RoleAssignmentRequest, response_model=ApiResponse)
def assign_user_role(request: Request, user_id: str, payload: RoleAssignmentRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "user:manage")
    if denial is not None:
        return denial
    rbac = _get_rbac(request)
    role = str(payload.role or "").strip()
    result = rbac.assign_role(user_id, role, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "rbac.role.assign", "user_id": user_id})
