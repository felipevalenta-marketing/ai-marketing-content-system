"""Markdown report endpoint."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, MarkdownReportRequest
from src.rbac.rbac_dependencies import authorize_request
from src.reports.markdown_generator import MarkdownReportGenerator


router = APIRouter(tags=["reports"])


@router.post("/reports/markdown", summary="Generate a markdown report", description="Render a professional markdown report from structured payloads.", request_model=MarkdownReportRequest, response_model=ApiResponse)
def generate_markdown_report(request: Request, payload: MarkdownReportRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "report:create")
    if denial is not None:
        return denial
    generator = get_service(request, "markdown_report")
    if generator is None:
        generator = MarkdownReportGenerator()
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = generator.generate_report(request_payload)
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "reports/markdown"})


@router.get("/reports/latest", summary="Get latest report metadata", description="Return the latest persisted report metadata when available.", response_model=ApiResponse)
def latest_report(request: Request) -> dict[str, Any]:
    user, denial = authorize_request(request, "report:read")
    if denial is not None:
        return denial
    storage = get_service(request, "storage")
    if storage is None:
        return build_api_response(success=False, data=None, errors=["Storage service is unavailable."], metadata={"route": "reports/latest"})
    latest = storage.reader.latest_records("report", limit=1) if getattr(storage, "reader", None) else storage.list_records("report")
    data = latest[0] if latest else {}
    return build_api_response(success=True, data=data, metadata={"route": "reports/latest", "count": len(latest)})
