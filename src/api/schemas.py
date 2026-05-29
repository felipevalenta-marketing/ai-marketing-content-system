"""Pydantic request and response schemas for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(value).strip()] if str(value).strip() else []


class BaseApiModel(BaseModel):
    class Config:
        extra = "ignore"


class GenerateRequest(BaseApiModel):
    brand: str = Field(default="wenzel_partner", examples=["wenzel_partner"])
    platform: str = Field(default="instagram", examples=["instagram"])
    content_type: str = Field(default="instagram_post", examples=["instagram_post"])
    organization_id: str = Field(default="")
    team_id: str = Field(default="")
    campaign_type: str | None = None
    objective: str = Field(default="generate_leads", examples=["generate_leads"])
    audience: str = Field(default="general")
    location: str = Field(default="")
    property_type: str = Field(default="")
    visual_style: str | None = None
    creative_direction: str | None = None
    image_type: str | None = None
    aspect_ratio: str | None = None
    video_type: str | None = None
    duration: str | None = None
    extra_notes: str = Field(default="")
    report: bool = True
    markdown: bool = False
    persist: bool = False
    dry_run: bool = False
    workflow: bool = False
    report_type: str | None = None
    platforms: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)

    @field_validator("platforms", "assets", mode="before")
    @classmethod
    def _validate_list_fields(cls, value: Any) -> list[str]:
        return _coerce_list(value)


class WorkflowRequest(BaseApiModel):
    workflow_type: str = Field(default="full_campaign_package")
    brand: str = Field(default="wenzel_partner")
    platform: str = Field(default="instagram")
    organization_id: str = Field(default="")
    team_id: str = Field(default="")
    platforms: list[str] = Field(default_factory=list)
    content_type: str = Field(default="instagram_post")
    campaign_type: str = Field(default="property_launch")
    objective: str = Field(default="generate_leads")
    audience: str = Field(default="general")
    location: str = Field(default="")
    property_type: str = Field(default="")
    visual_style: str | None = None
    creative_direction: str | None = None
    assets: list[str] = Field(default_factory=list)
    report: bool = True
    persist: bool = False
    dry_run: bool = False
    markdown: bool = False
    extra_notes: str = Field(default="")

    @field_validator("platforms", "assets", mode="before")
    @classmethod
    def _validate_list_fields(cls, value: Any) -> list[str]:
        return _coerce_list(value)


class CampaignRequest(BaseApiModel):
    brand: str = Field(default="wenzel_partner")
    organization_id: str = Field(default="")
    team_id: str = Field(default="")
    campaign_type: str = Field(default="property_launch")
    objective: str = Field(default="generate_leads")
    audience: str = Field(default="general")
    location: str = Field(default="")
    property_type: str = Field(default="")
    platforms: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    extra_notes: str = Field(default="")
    report: bool = True
    persist: bool = False
    dry_run: bool = False
    markdown: bool = False

    @field_validator("platforms", "assets", mode="before")
    @classmethod
    def _validate_list_fields(cls, value: Any) -> list[str]:
        return _coerce_list(value)


class AssetRequest(BaseApiModel):
    brand: str = Field(default="wenzel_partner")
    organization_id: str = Field(default="")
    team_id: str = Field(default="")
    campaign_type: str = Field(default="property_launch")
    objective: str = Field(default="generate_leads")
    audience: str = Field(default="general")
    location: str = Field(default="")
    property_type: str = Field(default="")
    platforms: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    visual_style: str | None = None
    creative_direction: str | None = None
    extra_notes: str = Field(default="")
    report: bool = True
    persist: bool = False
    dry_run: bool = False
    markdown: bool = False

    @field_validator("platforms", "assets", mode="before")
    @classmethod
    def _validate_list_fields(cls, value: Any) -> list[str]:
        return _coerce_list(value)


class MarkdownReportRequest(BaseApiModel):
    report_type: str = Field(default="execution_report")
    title: str = Field(default="Report")
    brand: str = Field(default="wenzel_partner")
    organization_id: str = Field(default="")
    team_id: str = Field(default="")
    platform: str = Field(default="instagram")
    campaign_type: str = Field(default="")
    content_type: str = Field(default="")
    workflow_result: dict[str, Any] = Field(default_factory=dict)
    pipeline_result: dict[str, Any] = Field(default_factory=dict)
    campaign_result: dict[str, Any] = Field(default_factory=dict)
    asset_result: dict[str, Any] = Field(default_factory=dict)
    governance_result: dict[str, Any] = Field(default_factory=dict)
    token_summary: dict[str, Any] = Field(default_factory=dict)
    cost_summary: dict[str, Any] = Field(default_factory=dict)
    storage_summary: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    export_markdown_report: bool = False


class AnalyticsRequest(BaseApiModel):
    analytics_type: str = Field(default="executive_dashboard")
    brand: str = Field(default="")
    platform: str = Field(default="")
    organization_id: str = Field(default="")
    team_id: str = Field(default="")
    date_range: dict[str, str] = Field(default_factory=lambda: {"start": "", "end": ""})
    filters: dict[str, Any] = Field(default_factory=dict)
    include_storage: bool = True
    include_tokens: bool = True
    include_costs: bool = True
    include_governance: bool = True
    include_reports: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class StorageRecordQuery(BaseApiModel):
    record_type: str | None = None
    record_id: str | None = None
    organization_id: str | None = None
    team_id: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


class ApiResponse(BaseApiModel):
    success: bool
    data: Any | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(ApiResponse):
    success: bool = False


class RegisterRequest(BaseApiModel):
    email: str = Field(default="")
    password: str = Field(default="")
    display_name: str = Field(default="")


class LoginRequest(BaseApiModel):
    email: str = Field(default="")
    password: str = Field(default="")


class UserProfileUpdateRequest(BaseApiModel):
    display_name: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)


class RoleAssignmentRequest(BaseApiModel):
    role: str = Field(default="viewer")


class FeatureFlagUpdateRequest(BaseApiModel):
    enabled: bool = True


class UserProfileResponse(BaseApiModel):
    user_id: str = ""
    email: str = ""
    display_name: str = ""
    status: str = "active"
    role: str = "viewer"
    permissions: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    active_organization_id: str = ""
    active_team_id: str = ""
    created_at: str = ""
    updated_at: str = ""
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuthResponse(BaseApiModel):
    access_token: str = ""
    token_type: str = "bearer"
    user: UserProfileResponse = Field(default_factory=UserProfileResponse)


class OrganizationSettingsRequest(BaseApiModel):
    default_brand: str = "wenzel_partner"
    default_platform: str = "instagram"
    default_language: str = "en"
    timezone: str = "Europe/Madrid"
    features: dict[str, Any] = Field(default_factory=dict)
    limits: dict[str, Any] = Field(default_factory=dict)


class OrganizationRequest(BaseApiModel):
    name: str = Field(default="")
    slug: str | None = None
    status: str = "active"
    owner_user_id: str | None = None
    settings: OrganizationSettingsRequest = Field(default_factory=OrganizationSettingsRequest)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrganizationUpdateRequest(BaseApiModel):
    name: str | None = None
    slug: str | None = None
    status: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TeamRequest(BaseApiModel):
    name: str = Field(default="")
    slug: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class TeamUpdateRequest(BaseApiModel):
    name: str | None = None
    slug: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MembershipRequest(BaseApiModel):
    user_id: str = Field(default="")
    role: str = Field(default="member")
    team_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MembershipUpdateRequest(BaseApiModel):
    role: str = Field(default="member")
    metadata: dict[str, Any] = Field(default_factory=dict)


class BrandAccessRequest(BaseApiModel):
    brand_id: str = Field(default="")
    access_level: str = Field(default="use")
    metadata: dict[str, Any] = Field(default_factory=dict)
