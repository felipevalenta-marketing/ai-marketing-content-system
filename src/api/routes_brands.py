"""Brand management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response


router = APIRouter(prefix="/brands", tags=["brands"])


def _manager(request: Request):
    services = getattr(request.app.state, "services", {})
    return services.get("brands")


def _query_bool(request: Request, key: str, fallback: bool = False) -> bool:
    raw = request.query_params.get(key)
    if raw is None:
        return bool(fallback)
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


@router.get("", summary="List brands", description="Return the available brand profiles.")
def list_brands(request: Request, active_only: bool = False, include_invalid: bool = False) -> dict[str, object]:
    manager = _manager(request)
    if manager is None:
        return build_api_response(success=False, data=None, errors=["Brand manager unavailable."], metadata={"route": "brands.list"})
    active_only = _query_bool(request, "active_only", active_only)
    include_invalid = _query_bool(request, "include_invalid", include_invalid)
    result = manager.list_brands(active_only=active_only, include_invalid=include_invalid)
    return build_api_response(success=bool(result.get("success", True)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "brands.list"})


@router.get("/{brand_id}", summary="Get brand profile", description="Return a safe profile for a specific brand.")
def get_brand(brand_id: str, request: Request) -> dict[str, object]:
    manager = _manager(request)
    if manager is None:
        return build_api_response(success=False, data=None, errors=["Brand manager unavailable."], metadata={"route": "brands.get"})
    result = manager.get_brand(brand_id)
    return build_api_response(success=bool(result.get("success", True)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "brands.get", "brand_id": brand_id})


@router.get("/{brand_id}/validate", summary="Validate brand", description="Validate a brand folder and its recommended files.")
def validate_brand(brand_id: str, request: Request) -> dict[str, object]:
    manager = _manager(request)
    if manager is None:
        return build_api_response(success=False, data=None, errors=["Brand manager unavailable."], metadata={"route": "brands.validate"})
    result = manager.validate_brand(brand_id)
    return build_api_response(success=bool(result.get("success", True)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "brands.validate", "brand_id": brand_id})


@router.get("/{brand_id}/defaults", summary="Get brand defaults", description="Return safe defaults for a brand.")
def brand_defaults(brand_id: str, request: Request) -> dict[str, object]:
    manager = _manager(request)
    if manager is None:
        return build_api_response(success=False, data=None, errors=["Brand manager unavailable."], metadata={"route": "brands.defaults"})
    result = manager.get_brand_defaults(brand_id)
    return build_api_response(success=bool(result.get("success", True)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "brands.defaults", "brand_id": brand_id})


@router.get("/{brand_id}/health", summary="Get brand health", description="Return a safe health score for a brand.")
def brand_health(brand_id: str, request: Request) -> dict[str, object]:
    manager = _manager(request)
    if manager is None:
        return build_api_response(success=False, data=None, errors=["Brand manager unavailable."], metadata={"route": "brands.health"})
    result = manager.get_brand_health(brand_id)
    return build_api_response(success=bool(result.get("success", True)), data=result, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "brands.health", "brand_id": brand_id})
