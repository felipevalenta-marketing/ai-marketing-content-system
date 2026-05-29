"""Organization, membership, and brand access API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from src.api.api_result import build_api_response
from src.api.runtime import get_service
from src.api.schemas import ApiResponse, BrandAccessRequest, MembershipRequest, MembershipUpdateRequest, OrganizationRequest, OrganizationUpdateRequest
from src.auth.current_user import get_current_user_result
from src.rbac.rbac_dependencies import authorize_request, authorize_request_any
from src.rbac.rbac_manager import RBACManager
from src.users.user_manager import UserManager


router = APIRouter(tags=["organizations"])


def _rbac(request: Request) -> RBACManager:
    rbac = get_service(request, "rbac")
    if rbac is not None:
        return rbac
    return RBACManager(UserManager())


def _organizations(request: Request):
    organization_manager = get_service(request, "organizations")
    if organization_manager is not None:
        return organization_manager
    from src.organizations.organization_manager import OrganizationManager

    return OrganizationManager()


def _memberships(request: Request):
    memberships = get_service(request, "memberships")
    if memberships is not None:
        return memberships
    return _organizations(request).membership_manager


def _brand_access(request: Request):
    brand_access = get_service(request, "brand_access")
    if brand_access is not None:
        return brand_access
    return _organizations(request).brand_access_manager


def _is_admin(user: dict[str, Any], rbac: RBACManager) -> bool:
    return rbac.has_any_permission(user, ["admin:all", "user:manage", "organization:manage_members"])


def _accessible_organization_ids(request: Request, user: dict[str, Any]) -> set[str]:
    memberships = _memberships(request).list_user_memberships(str(user.get("user_id", "")))
    org_ids = {str(item.get("organization_id", "")) for item in memberships.get("data", {}).get("memberships", [])}
    return {item for item in org_ids if item}


def _organization_access_denial(request: Request, user: dict[str, Any], organization_id: str) -> dict[str, Any] | None:
    manager = _organizations(request)
    rbac = _rbac(request)
    if _is_admin(user, rbac):
        return None
    if organization_id not in _accessible_organization_ids(request, user):
        return build_api_response(success=False, data=None, errors=["Organization access is forbidden."], metadata={"route": "organizations.access", "organization_id": organization_id})
    if not manager.can_user_access_organization(str(user.get("user_id", "")), organization_id):
        return build_api_response(success=False, data=None, errors=["Organization access is forbidden."], metadata={"route": "organizations.access", "organization_id": organization_id})
    return None


@router.get("/organizations", summary="List organizations", description="List organizations visible to the current user.", response_model=ApiResponse)
def list_organizations(request: Request) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:read")
    if denial is not None:
        return denial
    manager = _organizations(request)
    rbac = _rbac(request)
    if _is_admin(user, rbac):
        result = manager.list_organizations()
    else:
        result = manager.list_organizations(user_id=str(user.get("user_id", "")))
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.list"})


@router.post("/organizations", summary="Create organization", description="Create a new organization.", request_model=OrganizationRequest, response_model=ApiResponse)
def create_organization(request: Request, payload: OrganizationRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:create")
    if denial is not None:
        return denial
    manager = _organizations(request)
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = manager.create_organization(request_payload, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.create"})


@router.get("/organizations/{organization_id}", summary="Get organization", description="Return an organization profile.", response_model=ApiResponse)
def get_organization(request: Request, organization_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:read")
    if denial is not None:
        return denial
    manager = _organizations(request)
    org_denial = _organization_access_denial(request, user, organization_id)
    if org_denial is not None:
        return org_denial
    profile = manager.build_organization_profile(organization_id)
    if not profile:
        return build_api_response(success=False, data=None, errors=["Organization not found."], metadata={"route": "organizations.get", "organization_id": organization_id})
    return build_api_response(success=True, data=profile, metadata={"route": "organizations.get", "organization_id": organization_id})


@router.patch("/organizations/{organization_id}", summary="Update organization", description="Update an organization.", request_model=OrganizationUpdateRequest, response_model=ApiResponse)
def update_organization(request: Request, organization_id: str, payload: OrganizationUpdateRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:update")
    if denial is not None:
        return denial
    manager = _organizations(request)
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = manager.update_organization(organization_id, request_payload, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.update", "organization_id": organization_id})


def delete_organization(request: Request, organization_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:delete")
    if denial is not None:
        return denial
    manager = _organizations(request)
    result = manager.deactivate_organization(organization_id, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.delete", "organization_id": organization_id})


router.add_api_route(
    "/organizations/{organization_id}",
    delete_organization,
    methods=["DELETE"],
    summary="Deactivate organization",
    description="Deactivate an organization.",
    response_model=ApiResponse,
)


@router.get("/organizations/{organization_id}/members", summary="List organization members", description="List organization memberships.", response_model=ApiResponse)
def list_members(request: Request, organization_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:read")
    if denial is not None:
        return denial
    memberships = _memberships(request)
    org_denial = _organization_access_denial(request, user, organization_id)
    if org_denial is not None:
        return org_denial
    result = memberships.list_members(organization_id)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.members.list", "organization_id": organization_id})


@router.post("/organizations/{organization_id}/members", summary="Add organization member", description="Add a member to an organization.", request_model=MembershipRequest, response_model=ApiResponse)
def add_member(request: Request, organization_id: str, payload: MembershipRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:manage_members")
    if denial is not None:
        return denial
    memberships = _memberships(request)
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = memberships.add_member(organization_id, request_payload.get("user_id", ""), role=request_payload.get("role", "member"), team_id=request_payload.get("team_id"), actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.members.add", "organization_id": organization_id})


@router.patch("/memberships/{membership_id}", summary="Update membership role", description="Update a membership role.", request_model=MembershipUpdateRequest, response_model=ApiResponse)
def update_membership(request: Request, membership_id: str, payload: MembershipUpdateRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:manage_members")
    if denial is not None:
        return denial
    memberships = _memberships(request)
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = memberships.update_member_role(membership_id, request_payload.get("role", "member"), actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.members.update", "membership_id": membership_id})


def remove_membership(request: Request, membership_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:manage_members")
    if denial is not None:
        return denial
    memberships = _memberships(request)
    result = memberships.remove_member(membership_id, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.members.remove", "membership_id": membership_id})


router.add_api_route(
    "/memberships/{membership_id}",
    remove_membership,
    methods=["DELETE"],
    summary="Remove membership",
    description="Remove a member from an organization.",
    response_model=ApiResponse,
)


@router.get("/organizations/{organization_id}/brands", summary="List organization brands", description="List brand access entries for an organization.", response_model=ApiResponse)
def list_organization_brands(request: Request, organization_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "brand_access:read")
    if denial is not None:
        return denial
    org_denial = _organization_access_denial(request, user, organization_id)
    if org_denial is not None:
        return org_denial
    brand_access = _brand_access(request)
    result = brand_access.list_organization_brands(organization_id)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.brands.list", "organization_id": organization_id})


@router.post("/organizations/{organization_id}/brands", summary="Grant brand access", description="Grant brand access to an organization.", request_model=BrandAccessRequest, response_model=ApiResponse)
def grant_brand_access(request: Request, organization_id: str, payload: BrandAccessRequest) -> dict[str, Any]:
    user, denial = authorize_request(request, "brand_access:manage")
    if denial is not None:
        return denial
    brand_access = _brand_access(request)
    request_payload = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    result = brand_access.grant_brand_access(organization_id, request_payload.get("brand_id", ""), access_level=request_payload.get("access_level", "use"), actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.brands.add", "organization_id": organization_id})


def revoke_brand_access(request: Request, organization_id: str, brand_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "brand_access:manage")
    if denial is not None:
        return denial
    brand_access = _brand_access(request)
    result = brand_access.revoke_brand_access(organization_id, brand_id, actor=user)
    return build_api_response(success=bool(result.get("success", False)), data=result.get("data", {}), warnings=result.get("warnings", []), errors=result.get("errors", []), metadata={"route": "organizations.brands.remove", "organization_id": organization_id, "brand_id": brand_id})


router.add_api_route(
    "/organizations/{organization_id}/brands/{brand_id}",
    revoke_brand_access,
    methods=["DELETE"],
    summary="Revoke brand access",
    description="Revoke brand access from an organization.",
    response_model=ApiResponse,
)


@router.get("/organizations/{organization_id}/profile", summary="Get organization profile", description="Return aggregated organization profile.", response_model=ApiResponse)
def get_organization_profile(request: Request, organization_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:read")
    if denial is not None:
        return denial
    org_denial = _organization_access_denial(request, user, organization_id)
    if org_denial is not None:
        return org_denial
    manager = _organizations(request)
    profile = manager.build_organization_profile(organization_id)
    if not profile:
        return build_api_response(success=False, data=None, errors=["Organization not found."], metadata={"route": "organizations.profile", "organization_id": organization_id})
    return build_api_response(success=True, data=profile, metadata={"route": "organizations.profile", "organization_id": organization_id})


@router.get("/organizations/{organization_id}/health", summary="Get organization health", description="Return organization health metrics.", response_model=ApiResponse)
def get_organization_health(request: Request, organization_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:read")
    if denial is not None:
        return denial
    org_denial = _organization_access_denial(request, user, organization_id)
    if org_denial is not None:
        return org_denial
    manager = _organizations(request)
    health = manager.get_organization_health(organization_id)
    if not health:
        return build_api_response(success=False, data=None, errors=["Organization not found."], metadata={"route": "organizations.health", "organization_id": organization_id})
    return build_api_response(success=True, data=health, metadata={"route": "organizations.health", "organization_id": organization_id})


@router.get("/organizations/{organization_id}/context", summary="Get organization context", description="Return active organization context.", response_model=ApiResponse)
def get_organization_context(request: Request, organization_id: str) -> dict[str, Any]:
    user, denial = authorize_request(request, "organization:read")
    if denial is not None:
        return denial
    org_denial = _organization_access_denial(request, user, organization_id)
    if org_denial is not None:
        return org_denial
    manager = _organizations(request)
    context = manager.get_organization_context(organization_id, team_id=str(user.get("active_team_id", "")), brand_id=str(user.get("active_brand_id", "")) if user.get("active_brand_id") else None, user=user)
    validation = context.get("validation", {})
    if not context:
        return build_api_response(success=False, data=None, errors=["Organization not found."], metadata={"route": "organizations.context", "organization_id": organization_id})
    return build_api_response(success=bool(validation.get("valid", True)), data=context, warnings=validation.get("warnings", []), errors=validation.get("errors", []), metadata={"route": "organizations.context", "organization_id": organization_id})
