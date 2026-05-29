"""Storage record endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse
from src.rbac.rbac_dependencies import authorize_request


router = APIRouter(tags=["storage"])


@router.get("/storage/records", summary="List storage records", description="List stored records from the local persistence layer.", response_model=ApiResponse)
def list_records(request: Request) -> dict[str, Any]:
    user, denial = authorize_request(request, "storage:read")
    if denial is not None:
        return denial
    storage = get_service(request, "storage")
    if storage is None:
        return build_api_response(success=False, data=None, errors=["Storage service is unavailable."], metadata={"route": "storage/records"})
    record_type = request.query_params.get("record_type") if getattr(request, "query_params", None) else None
    records = storage.list_records(record_type=record_type or None)
    return build_api_response(success=True, data={"records": records, "count": len(records), "record_type": record_type or None}, metadata={"route": "storage/records"})


@router.get("/storage/records/{record_type}", summary="List records by type", description="List stored records by record type.", response_model=ApiResponse)
def list_records_by_type(request: Request, record_type: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "storage:read")
    if denial is not None:
        return denial
    storage = get_service(request, "storage")
    if storage is None:
        return build_api_response(success=False, data=None, errors=["Storage service is unavailable."], metadata={"route": "storage/records/type"})
    records = storage.list_records(record_type=record_type)
    return build_api_response(success=True, data={"records": records, "count": len(records), "record_type": record_type}, metadata={"route": "storage/records/type"})


@router.get("/storage/records/{record_type}/{record_id}", summary="Load a stored record", description="Load a single local storage record by type and identifier.", response_model=ApiResponse)
def load_record(request: Request, record_type: str, record_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "storage:read")
    if denial is not None:
        return denial
    storage = get_service(request, "storage")
    if storage is None:
        return build_api_response(success=False, data=None, errors=["Storage service is unavailable."], metadata={"route": "storage/records/item"})
    result = storage.load_record(record_type, record_id)
    return build_api_response(success=bool(result.get("success", False)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "storage/records/item"})
