"""Security hardening API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse
from src.auth.current_user import get_current_user_result
from src.security.security_health import build_security_baseline, build_security_health
from src.security.security_policy import build_security_policy


router = APIRouter(tags=["security"])


def _require_security_access(request: Request) -> tuple[dict[str, Any] | None, tuple[dict[str, Any], int] | None]:
    current = get_current_user_result(request)
    if not current.get("success"):
        return None, (build_api_response(success=False, data=None, warnings=current.get("warnings", []), errors=current.get("errors", []), metadata={"route": "security"}), 401)
    user = current.get("user", {}) if isinstance(current.get("user"), dict) else {}
    role = str(user.get("role", "")).strip().lower()
    if role not in {"admin", "manager"}:
        return None, (build_api_response(success=False, data=None, warnings=[], errors=["Forbidden."], metadata={"route": "security"}), 403)
    return user, None


def _get_security_manager(request: Request):
    security = get_service(request, "security")
    if security is not None:
        return security
    from src.security.security_manager import SecurityManager

    return SecurityManager(get_service(request, "configuration"))


@router.get("/security/status", summary="Security status", description="Return the security hardening summary.", response_model=ApiResponse)
def get_status(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_security_access(request)
    if denial is not None:
        return denial
    manager = _get_security_manager(request)
    summary = manager.build_security_summary(app=request.app)
    return build_api_response(success=True, data=summary, metadata={"route": "security.status", "user_id": user.get("user_id", "")})


@router.get("/security/health", summary="Security health", description="Return security health and readiness.", response_model=ApiResponse)
def get_health(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_security_access(request)
    if denial is not None:
        return denial
    manager = _get_security_manager(request)
    health = manager.get_security_status(app=request.app)
    return build_api_response(success=True, data=health, metadata={"route": "security.health", "user_id": user.get("user_id", "")})


@router.get("/security/baseline", summary="Security baseline", description="Return the MVP security baseline readiness.", response_model=ApiResponse)
def get_baseline(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_security_access(request)
    if denial is not None:
        return denial
    baseline = build_security_baseline(request.app)
    return build_api_response(success=True, data=baseline, metadata={"route": "security.baseline", "user_id": user.get("user_id", "")})


@router.get("/security/findings", summary="Security findings", description="Return sanitized security findings.", response_model=ApiResponse)
def get_findings(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_security_access(request)
    if denial is not None:
        return denial
    manager = _get_security_manager(request)
    report = manager.validate_security(app=request.app)
    findings = list(report.get("secret_scan", {}).get("findings", []))
    data = {
        "secret_scan": report.get("secret_scan", {}),
        "findings": findings,
        "count": len(findings),
        "warnings": report.get("warnings", []),
        "errors": report.get("errors", []),
    }
    return build_api_response(success=True, data=data, metadata={"route": "security.findings", "user_id": user.get("user_id", "")})


@router.get("/security/dependencies", summary="Security dependencies", description="Return dependency validation results.", response_model=ApiResponse)
def get_dependencies(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_security_access(request)
    if denial is not None:
        return denial
    manager = _get_security_manager(request)
    report = manager.build_dependency_report()
    data = report.get("data", report) if isinstance(report, dict) else report
    return build_api_response(success=True, data=data, metadata={"route": "security.dependencies", "user_id": user.get("user_id", "")})


@router.get("/security/configuration", summary="Security configuration", description="Return active security configuration flags.", response_model=ApiResponse)
def get_configuration(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_security_access(request)
    if denial is not None:
        return denial
    manager = _get_security_manager(request)
    summary = manager.build_security_summary(app=request.app)
    data = {
        "security_enabled": summary.get("active_protections", {}).get("security_headers", True) or summary.get("security_ready", False),
        "active_protections": summary.get("active_protections", {}),
        "configuration": summary.get("metadata", {}).get("system_status", {}),
        "release_ready": summary.get("release_ready", False),
    }
    return build_api_response(success=True, data=data, metadata={"route": "security.configuration", "user_id": user.get("user_id", "")})


@router.get("/security/policy", summary="Security policy", description="Return the MVP security policy and CORS compatibility summary.", response_model=ApiResponse)
def get_policy(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_security_access(request)
    if denial is not None:
        return denial
    policy = build_security_policy(request.app)
    return build_api_response(success=True, data=policy, metadata={"route": "security.policy", "user_id": user.get("user_id", "")})
