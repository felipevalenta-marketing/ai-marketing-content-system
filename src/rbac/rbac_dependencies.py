"""FastAPI helpers for RBAC-enforced routes."""

from __future__ import annotations

from typing import Any, Callable

from fastapi import HTTPException, Request

from src.auth.current_user import get_current_user_result
from src.rbac.permission_checker import check_permission
from src.rbac.rbac_result import build_permission_denied_result


def _current_user_or_401(request: Request) -> dict[str, Any]:
    result = get_current_user_result(request)
    if not result.get("success"):
        raise HTTPException(401, result.get("errors", ["Authentication required."])[0])
    return result.get("user", {}) if isinstance(result.get("user"), dict) else {}


def authorize_request(request: Request, permission: str) -> tuple[dict[str, Any] | None, tuple[dict[str, Any], int] | None]:
    current = get_current_user_result(request)
    if not current.get("success"):
        return None, ({"success": False, "data": None, "warnings": current.get("warnings", []), "errors": current.get("errors", []), "metadata": {"route": "auth"}}, 401)
    user = current.get("user", {}) if isinstance(current.get("user"), dict) else {}
    result = check_permission(user, permission)
    if not result.get("allowed"):
        denial = build_permission_denied_result(permission, str(user.get("role", "viewer")), reason=result.get("reason", "Forbidden."), errors=result.get("errors", []))
        return None, ({"success": False, "data": denial, "warnings": denial.get("warnings", []), "errors": denial.get("errors", []), "metadata": {"route": "rbac"}}, 403)
    return user, None


def authorize_request_any(request: Request, permissions: list[str]) -> tuple[dict[str, Any] | None, tuple[dict[str, Any], int] | None]:
    current = get_current_user_result(request)
    if not current.get("success"):
        return None, ({"success": False, "data": None, "warnings": current.get("warnings", []), "errors": current.get("errors", []), "metadata": {"route": "auth"}}, 401)
    user = current.get("user", {}) if isinstance(current.get("user"), dict) else {}
    rbac = getattr(request.app.state, "services", {}).get("rbac")
    if rbac is None:
        from src.rbac.rbac_manager import RBACManager
        from src.users.user_manager import UserManager

        rbac = RBACManager(UserManager())
    if permissions and not rbac.has_any_permission(user, permissions):
        return None, ({"success": False, "data": build_permission_denied_result(permissions[0], str(user.get("role", "viewer")), reason="Forbidden.", errors=["Forbidden."]), "warnings": [], "errors": ["Forbidden."], "metadata": {"route": "rbac"}}, 403)
    return user, None


def require_permission(permission: str) -> Callable[[Request], dict[str, Any]]:
    def dependency(request: Request) -> dict[str, Any]:
        user = _current_user_or_401(request)
        result = check_permission(user, permission)
        if not result.get("allowed"):
            raise HTTPException(403, result.get("reason", "Forbidden."))
        return user

    return dependency


def require_any_permission(permissions: list[str]) -> Callable[[Request], dict[str, Any]]:
    def dependency(request: Request) -> dict[str, Any]:
        user = _current_user_or_401(request)
        rbac = getattr(request.app.state, "services", {}).get("rbac")
        if rbac is None or not rbac.has_any_permission(user, permissions):
            raise HTTPException(403, "Forbidden.")
        return user

    return dependency


def require_all_permissions(permissions: list[str]) -> Callable[[Request], dict[str, Any]]:
    def dependency(request: Request) -> dict[str, Any]:
        user = _current_user_or_401(request)
        rbac = getattr(request.app.state, "services", {}).get("rbac")
        if rbac is None or not rbac.has_all_permissions(user, permissions):
            raise HTTPException(403, "Forbidden.")
        return user

    return dependency


def require_role(role: str) -> Callable[[Request], dict[str, Any]]:
    def dependency(request: Request) -> dict[str, Any]:
        user = _current_user_or_401(request)
        current_role = str(user.get("role", "")).strip().lower()
        if current_role != str(role).strip().lower():
            raise HTTPException(403, "Forbidden.")
        return user

    return dependency
