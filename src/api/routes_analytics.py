"""Analytics API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.analytics.analytics_engine import AnalyticsEngine
from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import AnalyticsRequest, ApiResponse
from src.rbac.rbac_dependencies import authorize_request


router = APIRouter(tags=["analytics"])


def _get_engine(request: Request) -> AnalyticsEngine:
    engine = get_service(request, "analytics")
    if engine is None:
        storage = get_service(request, "storage")
        reporting = get_service(request, "reporting")
        engine = AnalyticsEngine(storage_manager=storage, reporting_engine=reporting)
    return engine


def _query_request(request: Request, analytics_type: str) -> dict[str, Any]:
    query = getattr(request, "query_params", {})
    date_range = {
        "start": query.get("start", "") if hasattr(query, "get") else "",
        "end": query.get("end", "") if hasattr(query, "get") else "",
    }
    filters = {
        key: query.get(key, "")
        for key in ("campaign_type", "content_type", "workflow_type", "asset_type", "brand", "platform")
        if hasattr(query, "get") and query.get(key)
    }
    return {
        "analytics_type": analytics_type,
        "brand": query.get("brand", "") if hasattr(query, "get") else "",
        "platform": query.get("platform", "") if hasattr(query, "get") else "",
        "date_range": date_range,
        "filters": filters,
        "include_storage": True,
        "include_tokens": True,
        "include_costs": True,
        "include_governance": True,
        "include_reports": True,
    }


@router.get("/analytics/health", summary="Analytics health", description="Return a safe analytics subsystem health summary.", response_model=ApiResponse)
def analytics_health(request: Request) -> dict[str, Any]:
    user, denial = authorize_request(request, "analytics:read")
    if denial is not None:
        return denial
    engine = _get_engine(request)
    result = engine.generate_analytics(_query_request(request, "api_health_analytics"))
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "analytics/health"})


@router.get("/analytics/summary", summary="Analytics summary", description="Return the executive dashboard analytics summary.", response_model=ApiResponse)
def analytics_summary(request: Request) -> dict[str, Any]:
    user, denial = authorize_request(request, "analytics:read")
    if denial is not None:
        return denial
    engine = _get_engine(request)
    result = engine.generate_executive_dashboard(_query_request(request, "executive_dashboard"))
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "analytics/summary"})


@router.get("/analytics/dashboard", summary="Analytics dashboard", description="Return a frontend-ready analytics dashboard payload.", response_model=ApiResponse)
def analytics_dashboard(request: Request) -> dict[str, Any]:
    user, denial = authorize_request(request, "analytics:read")
    if denial is not None:
        return denial
    engine = _get_engine(request)
    result = engine.build_dashboard_payload(_query_request(request, "executive_dashboard"))
    dashboard_payload = result.get("dashboard_payload", {})
    return build_api_response(success=bool(result.get("success", False)), data=dashboard_payload, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "analytics/dashboard"})


@router.post("/analytics/query", summary="Query analytics", description="Query the analytics layer with structured filters.", request_model=AnalyticsRequest, response_model=ApiResponse)
def analytics_query(request: Request, payload: AnalyticsRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "analytics:read")
    if denial is not None:
        return denial
    engine = _get_engine(request)
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = engine.generate_analytics(request_payload)
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "analytics/query"})
