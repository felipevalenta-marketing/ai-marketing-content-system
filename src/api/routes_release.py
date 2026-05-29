"""MVP release readiness API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse
from src.auth.current_user import get_current_user_result
from src.release.release_manager import ReleaseManager


router = APIRouter(tags=["release"])


def _require_release_access(request: Request) -> tuple[dict[str, Any] | None, tuple[dict[str, Any], int] | None]:
    current = get_current_user_result(request)
    if not current.get("success"):
        return None, (build_api_response(success=False, data=None, warnings=current.get("warnings", []), errors=current.get("errors", []), metadata={"route": "release"}), 401)
    user = current.get("user", {}) if isinstance(current.get("user"), dict) else {}
    role = str(user.get("role", "")).strip().lower()
    if role not in {"admin", "manager"}:
        return None, (build_api_response(success=False, data=None, warnings=[], errors=["Forbidden."], metadata={"route": "release"}), 403)
    return user, None


def _get_release_manager(request: Request) -> ReleaseManager:
    release = get_service(request, "release")
    if isinstance(release, ReleaseManager):
        return release
    return ReleaseManager()


@router.get("/release/status", summary="Release status", description="Return the MVP release summary.", response_model=ApiResponse)
def get_status(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    manager = _get_release_manager(request)
    summary = manager.build_release_summary(app=request.app)
    return build_api_response(success=True, data=summary, metadata={"route": "release.status", "user_id": user.get("user_id", "")})


@router.get("/release/certification", summary="Release certification", description="Return the final MVP certification.", response_model=ApiResponse)
def get_certification(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    certification = _get_release_manager(request).build_release_summary(app=request.app).get("certification", {})
    return build_api_response(success=True, data=certification, metadata={"route": "release.certification", "user_id": user.get("user_id", "")})


@router.get("/release/maturity", summary="Release maturity", description="Return the MVP maturity scoring.", response_model=ApiResponse)
def get_maturity(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    maturity = _get_release_manager(request).build_release_summary(app=request.app).get("maturity", {})
    return build_api_response(success=True, data=maturity, metadata={"route": "release.maturity", "user_id": user.get("user_id", "")})


@router.get("/release/governance", summary="Release governance", description="Return the release governance decision.", response_model=ApiResponse)
def get_governance(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    governance = _get_release_manager(request).build_release_summary(app=request.app).get("governance", {})
    return build_api_response(success=True, data=governance, metadata={"route": "release.governance", "user_id": user.get("user_id", "")})


@router.get("/release/executive-summary", summary="Executive summary", description="Return the MVP executive summary.", response_model=ApiResponse)
def get_executive_summary(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    summary = _get_release_manager(request).build_release_summary(app=request.app).get("executive_summary", "")
    return build_api_response(success=True, data={"content": summary, "generated": bool(summary), "path": "docs/MVP_EXECUTIVE_SUMMARY.md"}, metadata={"route": "release.executive_summary", "user_id": user.get("user_id", "")})


@router.get("/release/readiness", summary="Release readiness", description="Return the MVP acceptance summary.", response_model=ApiResponse)
def get_readiness(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    readiness = _get_release_manager(request).build_release_summary(app=request.app).get("mvp_acceptance", {})
    return build_api_response(success=True, data=readiness, metadata={"route": "release.readiness", "user_id": user.get("user_id", "")})


@router.get("/release/health", summary="Release health", description="Return release health status.", response_model=ApiResponse)
def get_health(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    health = _get_release_manager(request).build_release_summary(app=request.app).get("release_health", {})
    return build_api_response(success=True, data=health, metadata={"route": "release.health", "user_id": user.get("user_id", "")})


@router.get("/release/checklist", summary="Release checklist", description="Return the MVP release checklist.", response_model=ApiResponse)
def get_checklist(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    checklist = _get_release_manager(request).build_release_summary(app=request.app).get("release_checklist", {})
    return build_api_response(success=True, data=checklist, metadata={"route": "release.checklist", "user_id": user.get("user_id", "")})


@router.get("/release/report", summary="Release report", description="Generate and return the MVP readiness report.", response_model=ApiResponse)
def get_report(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    manager = _get_release_manager(request)
    summary = manager.build_release_summary(app=request.app)
    report = manager.generate_release_report(summary)
    data = {
        "generated": bool(report.get("generated", False)),
        "path": report.get("path", ""),
        "content": report.get("content", ""),
        "summary": summary,
    }
    return build_api_response(success=True, data=data, metadata={"route": "release.report", "user_id": user.get("user_id", "")})


@router.get("/release/score", summary="Release score", description="Return the MVP release score.", response_model=ApiResponse)
def get_score(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denial = _require_release_access(request)
    if denial is not None:
        return denial
    score = _get_release_manager(request).build_release_summary(app=request.app)
    data = {
        "release_score": score.get("release_score", 0),
        "release_status": score.get("release_status", "blocked"),
        "recommendations": score.get("recommendations", []),
        "factors": score.get("factors", {}),
    }
    return build_api_response(success=True, data=data, metadata={"route": "release.score", "user_id": user.get("user_id", "")})
