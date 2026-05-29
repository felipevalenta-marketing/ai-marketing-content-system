"""Helpers to resolve the current authenticated user from an API request."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request

from src.api.runtime import get_service


def extract_bearer_token(request: Any) -> str:
    headers = getattr(request, "headers", {}) or {}
    header_value = headers.get("authorization") or headers.get("Authorization") or ""
    value = str(header_value).strip()
    if value.lower().startswith("bearer "):
        return value.split(" ", 1)[1].strip()
    return ""


def get_current_user(request: Request) -> dict[str, Any]:
    auth_service = get_service(request, "auth")
    if auth_service is None:
        raise HTTPException(401, "Authentication service is unavailable.")
    token = extract_bearer_token(request)
    result = auth_service.authenticate(token)
    if not result.get("success"):
        message = result.get("errors", ["Authentication required."])[0]
        raise HTTPException(401, message)
    user = result.get("user", {})
    return user if isinstance(user, dict) else {}


def get_current_user_result(request: Request) -> dict[str, Any]:
    auth_service = get_service(request, "auth")
    if auth_service is None:
        return {"success": False, "user": {}, "access_token": "", "token_type": "bearer", "warnings": [], "errors": ["Authentication service is unavailable."], "metadata": {}}
    token = extract_bearer_token(request)
    result = auth_service.authenticate(token)
    if not isinstance(result, dict):
        return {"success": False, "user": {}, "access_token": "", "token_type": "bearer", "warnings": [], "errors": ["Authentication required."], "metadata": {}}
    return result


def require_current_user(request: Request) -> dict[str, Any]:
    return get_current_user(request)
