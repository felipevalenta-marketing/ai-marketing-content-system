"""User profile API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, UserProfileUpdateRequest
from src.auth.current_user import get_current_user_result
from src.rbac.rbac_dependencies import authorize_request


router = APIRouter(tags=["users"])


@router.get("/users", summary="List users", description="List safe user profiles.", response_model=ApiResponse)
def list_users(request: Request) -> dict[str, Any]:
    user, denial = authorize_request(request, "user:manage")
    if denial is not None:
        return denial
    user_manager = get_service(request, "users")
    if user_manager is None:
        return build_api_response(success=False, data=None, errors=["User service is unavailable."], metadata={"route": "users.list"})
    users = user_manager.list_users()
    return build_api_response(success=True, data={"users": users, "count": len(users)}, metadata={"route": "users.list"})


@router.get("/users/profile", summary="Get profile", description="Return the authenticated user's profile.", response_model=ApiResponse)
def get_profile(request: Request) -> dict[str, Any]:
    result = get_current_user_result(request)
    if not result.get("success"):
        return build_api_response(success=False, data=None, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "users.profile.get"}), 401
    return build_api_response(success=True, data=result.get("user", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "users.profile.get"})


@router.patch("/users/profile", summary="Update profile", description="Update the authenticated user's profile.", request_model=UserProfileUpdateRequest, response_model=ApiResponse)
def update_profile(request: Request, payload: UserProfileUpdateRequest) -> dict[str, Any]:
    current = get_current_user_result(request)
    if not current.get("success"):
        return build_api_response(success=False, data=None, warnings=current.get("warnings", []), errors=current.get("errors", []), metadata={"route": "users.profile.patch"}), 401
    user = current.get("user", {})
    user_manager = get_service(request, "users")
    if user_manager is None:
        return build_api_response(success=False, data=None, errors=["User service is unavailable."], metadata={"route": "users.profile.patch"})
    updates = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = user_manager.update_user(user.get("user_id", ""), updates, updated_by=user.get("user_id", ""))
    return build_api_response(success=bool(result.get("success", False)), data=result.get("user", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "users.profile.patch"})
