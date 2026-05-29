"""Observability API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse
from src.observability.error_tracker import get_error_tracker
from src.observability.observability_health import build_observability_configuration, build_observability_health, get_system_status_summary
from src.observability.metrics_collector import collect_metrics
from src.observability.metrics_registry import get_metrics_registry
from src.observability.runtime_monitor import build_runtime_diagnostics
from src.observability.storage_monitor import build_storage_observability
from src.observability.workflow_monitor import get_workflow_monitor
from src.rbac.rbac_dependencies import authorize_request


router = APIRouter(tags=["observability"])


def _require_observability_access(request: Request) -> tuple[dict[str, Any] | None, tuple[dict[str, Any], int] | None]:
    return authorize_request(request, "system:read")


@router.get("/observability/health", summary="Observability health", description="Return a safe observability health summary.", response_model=ApiResponse)
def observability_health(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    data = build_observability_health(request.app)
    return build_api_response(success=True, data=data, metadata={"route": "observability.health", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/status", summary="System status", description="Return the unified system status summary.", response_model=ApiResponse)
def observability_status(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    data = get_system_status_summary(request.app)
    return build_api_response(success=True, data=data, metadata={"route": "observability.status", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/domains", summary="Metric domains", description="Return grouped observability metric domains.", response_model=ApiResponse)
def observability_domains(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    registry = get_metrics_registry()
    data = {
        "domains": [{"domain": domain, **registry.get_domain_metrics(domain)} for domain in registry.list_domains()],
        "count": len(registry.list_domains()),
    }
    return build_api_response(success=True, data=data, metadata={"route": "observability.domains", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/metrics", summary="Observability metrics", description="Return safe runtime metrics.", response_model=ApiResponse)
def observability_metrics(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    data = collect_metrics()
    return build_api_response(success=True, data=data, metadata={"route": "observability.metrics", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/runtime", summary="Runtime diagnostics", description="Return safe runtime diagnostics.", response_model=ApiResponse)
def observability_runtime(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    data = build_runtime_diagnostics(request.app)
    return build_api_response(success=True, data=data, metadata={"route": "observability.runtime", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/errors", summary="Recent errors", description="Return recent sanitized errors.", response_model=ApiResponse)
def observability_errors(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    tracker = get_error_tracker()
    data = {"recent_errors": tracker.list_recent_errors(limit=20), "summary": tracker.summarize_errors()}
    return build_api_response(success=True, data=data, metadata={"route": "observability.errors", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/workflows", summary="Workflow observations", description="Return workflow monitoring summary.", response_model=ApiResponse)
def observability_workflows(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    workflow_metrics = get_workflow_monitor().get_metrics()
    data = {
        **workflow_metrics,
        "workflow_metrics": workflow_metrics,
        "workflow_summary": get_workflow_monitor().get_summary(),
    }
    return build_api_response(success=True, data=data, metadata={"route": "observability.workflows", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/storage", summary="Storage observations", description="Return storage monitoring summary.", response_model=ApiResponse)
def observability_storage(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    storage = get_service(request, "storage")
    data = build_storage_observability(storage)
    return build_api_response(success=True, data=data, metadata={"route": "observability.storage", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/tokens", summary="Token observability", description="Return token usage observability.", response_model=ApiResponse)
def observability_tokens(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    data = get_metrics_registry().get_domain_metrics("tokens")
    data = {**data, **(data.get("metrics", {}) if isinstance(data, dict) else {})}
    return build_api_response(success=True, data=data, metadata={"route": "observability.tokens", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/costs", summary="Cost observability", description="Return cost usage observability.", response_model=ApiResponse)
def observability_costs(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    data = get_metrics_registry().get_domain_metrics("costs")
    data = {**data, **(data.get("metrics", {}) if isinstance(data, dict) else {})}
    return build_api_response(success=True, data=data, metadata={"route": "observability.costs", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})


@router.get("/observability/configuration", summary="Observability configuration", description="Return active observability configuration.", response_model=ApiResponse)
def observability_configuration(request: Request) -> dict[str, Any] | tuple[dict[str, Any], int]:
    user, denied = _require_observability_access(request)
    if denied is not None:
        return denied
    data = build_observability_configuration(request.app)
    return build_api_response(success=True, data=data, metadata={"route": "observability.configuration", "user_id": user.get("user_id", "") if isinstance(user, dict) else ""})
