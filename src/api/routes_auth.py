"""Authentication API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, LoginRequest, RegisterRequest
from src.auth.current_user import extract_bearer_token, get_current_user_result


router = APIRouter(tags=["auth"])


@router.post("/auth/register", summary="Register user", description="Create a new user account and return a JWT.", request_model=RegisterRequest, response_model=ApiResponse)
def register(request: Request, payload: RegisterRequest) -> dict[str, Any]:
    auth_service = get_service(request, "auth")
    if auth_service is None:
        return build_api_response(success=False, data=None, errors=["Authentication service is unavailable."], metadata={"route": "auth.register"})
    result = auth_service.register(payload.email, payload.password, payload.display_name)
    data = {
        "access_token": result.get("access_token", ""),
        "token_type": result.get("token_type", "bearer"),
        "user": result.get("user", {}),
    }
    return build_api_response(success=bool(result.get("success", False)), data=data, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "auth.register"})


@router.post("/auth/login", summary="Login user", description="Authenticate a user and return a JWT.", request_model=LoginRequest, response_model=ApiResponse)
def login(request: Request, payload: LoginRequest) -> dict[str, Any]:
    auth_service = get_service(request, "auth")
    if auth_service is None:
        return build_api_response(success=False, data=None, errors=["Authentication service is unavailable."], metadata={"route": "auth.login"})
    result = auth_service.login(payload.email, payload.password)
    data = {
        "access_token": result.get("access_token", ""),
        "token_type": result.get("token_type", "bearer"),
        "user": result.get("user", {}),
    }
    return build_api_response(success=bool(result.get("success", False)), data=data, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "auth.login"})


@router.post("/auth/logout", summary="Logout user", description="Revoke the current JWT locally.", response_model=ApiResponse)
def logout(request: Request) -> dict[str, Any]:
    auth_service = get_service(request, "auth")
    if auth_service is None:
        return build_api_response(success=False, data=None, errors=["Authentication service is unavailable."], metadata={"route": "auth.logout"})
    token = extract_bearer_token(request)
    result = auth_service.logout(token)
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "auth.logout"})


@router.get("/auth/me", summary="Current user", description="Return the currently authenticated user.", response_model=ApiResponse)
def me(request: Request) -> dict[str, Any]:
    result = get_current_user_result(request)
    if not result.get("success"):
        return build_api_response(success=False, data=None, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "auth.me"}), 401
    return build_api_response(success=True, data=result.get("user", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "auth.me"})
