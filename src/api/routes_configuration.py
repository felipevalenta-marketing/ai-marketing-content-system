"""SaaS configuration API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_error, build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, FeatureFlagUpdateRequest
from src.auth.current_user import get_current_user_result
from src.rbac.rbac_dependencies import authorize_request_any


router = APIRouter(tags=["configuration"])


def _get_configuration_manager(request: Request):
    configuration = get_service(request, "configuration")
    if configuration is not None:
        return configuration
    from src.configuration.config_manager import ConfigManager

    return ConfigManager()


def _require_auth(request: Request):
    current = get_current_user_result(request)
    if not current.get("success"):
        return None, (build_api_response(success=False, data=None, warnings=current.get("warnings", []), errors=current.get("errors", []), metadata={"route": "configuration"}), 401)
    return current.get("user", {}), None


@router.get("/configuration", summary="Get configuration summary", description="Return the safe global SaaS configuration summary.", response_model=ApiResponse)
def get_configuration(request: Request) -> dict[str, Any]:
    user, denial = _require_auth(request)
    if denial is not None:
        return denial
    manager = _get_configuration_manager(request)
    result = manager.get_system_summary()
    return build_api_response(success=True, data=result, metadata={"route": "configuration"})


@router.get("/configuration/platform", summary="Get platform configuration", description="Return the safe platform configuration.", response_model=ApiResponse)
def get_platform(request: Request) -> dict[str, Any]:
    user, denial = _require_auth(request)
    if denial is not None:
        return denial
    manager = _get_configuration_manager(request)
    return build_api_response(success=True, data=manager.get_platform_config(), metadata={"route": "configuration.platform"})


@router.get("/configuration/features", summary="Get feature flags", description="Return the centralized feature flags.", response_model=ApiResponse)
def get_features(request: Request) -> dict[str, Any]:
    user, denial = _require_auth(request)
    if denial is not None:
        return denial
    manager = _get_configuration_manager(request)
    return build_api_response(success=True, data={"features": manager.get_feature_flags()}, metadata={"route": "configuration.features"})


@router.get("/configuration/modules", summary="Get module registry", description="Return the module registry.", response_model=ApiResponse)
def get_modules(request: Request) -> dict[str, Any]:
    user, denial = _require_auth(request)
    if denial is not None:
        return denial
    manager = _get_configuration_manager(request)
    return build_api_response(success=True, data={"modules": manager.get_module_registry()}, metadata={"route": "configuration.modules"})


@router.get("/configuration/limits", summary="Get limits", description="Return informational platform limits.", response_model=ApiResponse)
def get_limits(request: Request) -> dict[str, Any]:
    user, denial = _require_auth(request)
    if denial is not None:
        return denial
    manager = _get_configuration_manager(request)
    return build_api_response(success=True, data={"limits": manager.get_limits()}, metadata={"route": "configuration.limits"})


@router.get("/configuration/environment", summary="Get environment configuration", description="Return the environment configuration.", response_model=ApiResponse)
def get_environment(request: Request) -> dict[str, Any]:
    user, denial = _require_auth(request)
    if denial is not None:
        return denial
    manager = _get_configuration_manager(request)
    return build_api_response(success=True, data=manager.get_environment_config(), metadata={"route": "configuration.environment"})


@router.get("/configuration/health", summary="Get configuration health", description="Return configuration health metrics.", response_model=ApiResponse)
def get_health(request: Request) -> dict[str, Any]:
    user, denial = _require_auth(request)
    if denial is not None:
        return denial
    manager = _get_configuration_manager(request)
    return build_api_response(success=True, data=manager.get_configuration_health(), metadata={"route": "configuration.health"})


@router.patch("/configuration/features/{flag}", summary="Update feature flag", description="Update a feature flag when the caller has configuration management access.", response_model=ApiResponse)
def update_feature_flag(request: Request, flag: str, payload: FeatureFlagUpdateRequest) -> dict[str, Any]:
    user, denial = authorize_request_any(request, ["system:manage", "admin:all"])
    if denial is not None:
        return denial
    manager = _get_configuration_manager(request)
    enabled_value = payload.enabled if hasattr(payload, "enabled") else (payload or {}).get("enabled", None)
    if not isinstance(enabled_value, bool):
        error, status_code = build_api_error("Feature flag update requires a boolean enabled value.", metadata={"route": "configuration.features.update", "flag": flag}, status_code=422)
        return error, status_code
    result = manager.update_feature_flag(flag, enabled_value)
    if not result.get("success", False):
        error_message = result.get("errors", ["Feature flag update failed."])[0]
        error, status_code = build_api_error(error_message, metadata={"route": "configuration.features.update", "flag": flag}, warnings=result.get("warnings", []), status_code=400)
        return error, status_code
    summary = manager.get_system_summary()
    response_data = {
        **result,
        "configuration": summary,
    }
    return build_api_response(success=bool(result.get("success", False)), data=response_data, warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "configuration.features.update", "flag": flag})
