"""Organization contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class OrganizationContract:
    organization_id: str
    name: str
    slug: str
    status: str
    created_at: str
    updated_at: str
    owner_user_id: str
    settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "owner_user_id": self.owner_user_id,
            "settings": self.settings,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class OrganizationProfileContract(OrganizationContract):
    team_count: int = 0
    member_count: int = 0
    brand_count: int = 0
    active_brand_ids: list[str] = field(default_factory=list)
    health_score: int = 0
    health_status: str = "warning"
    warnings: list[str] = field(default_factory=list)
    teams: list[dict[str, Any]] = field(default_factory=list)
    members: list[dict[str, Any]] = field(default_factory=list)
    brands: list[dict[str, Any]] = field(default_factory=list)
    health: dict[str, Any] = field(default_factory=dict)
    organization: dict[str, Any] = field(default_factory=dict)
    tenant_ready: bool = True
    tenant_configuration: dict[str, Any] = field(default_factory=dict)
    tenant_limits: dict[str, Any] = field(default_factory=dict)
    analytics: dict[str, Any] = field(default_factory=dict)
    role_bridge: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update(
            {
                "team_count": self.team_count,
                "member_count": self.member_count,
                "brand_count": self.brand_count,
                "active_brand_ids": self.active_brand_ids,
                "health_score": self.health_score,
                "health_status": self.health_status,
                "warnings": self.warnings,
                "teams": self.teams,
                "members": self.members,
                "brands": self.brands,
                "health": self.health,
                "organization": self.organization,
                "tenant_ready": self.tenant_ready,
                "tenant_configuration": self.tenant_configuration,
                "tenant_limits": self.tenant_limits,
                "analytics": self.analytics,
                "role_bridge": self.role_bridge,
            }
        )
        return data


@dataclass(frozen=True)
class OrganizationHealthContract:
    health_score: int
    health_status: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_score": self.health_score,
            "health_status": self.health_status,
            "warnings": self.warnings,
        }


@dataclass(frozen=True)
class OrganizationContextContract:
    organization_id: str
    team_id: str = ""
    brand_id: str = ""
    tenant_ready: bool = True
    organization: dict[str, Any] = field(default_factory=dict)
    organization_profile: dict[str, Any] = field(default_factory=dict)
    active_team: dict[str, Any] = field(default_factory=dict)
    active_brand: dict[str, Any] = field(default_factory=dict)
    teams: list[dict[str, Any]] = field(default_factory=list)
    members: list[dict[str, Any]] = field(default_factory=list)
    brands: list[dict[str, Any]] = field(default_factory=list)
    role_bridge: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "team_id": self.team_id,
            "brand_id": self.brand_id,
            "tenant_ready": self.tenant_ready,
            "organization": self.organization,
            "organization_profile": self.organization_profile,
            "active_team": self.active_team,
            "active_brand": self.active_brand,
            "teams": self.teams,
            "members": self.members,
            "brands": self.brands,
            "role_bridge": self.role_bridge,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TenantContract:
    tenant_ready: bool
    tenant_isolation: bool = False
    tenant_configuration: dict[str, Any] = field(default_factory=dict)
    tenant_limits: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_ready": self.tenant_ready,
            "tenant_isolation": self.tenant_isolation,
            "tenant_configuration": self.tenant_configuration,
            "tenant_limits": self.tenant_limits,
        }


@dataclass(frozen=True)
class OrganizationInvitationContract:
    email: str
    organization_id: str
    role: str

    def to_dict(self) -> dict[str, Any]:
        return {"email": self.email, "organization_id": self.organization_id, "role": self.role}


@dataclass(frozen=True)
class OrganizationSettingsContract:
    default_brand: str
    default_platform: str
    default_language: str
    timezone: str
    features: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "default_brand": self.default_brand,
            "default_platform": self.default_platform,
            "default_language": self.default_language,
            "timezone": self.timezone,
            "features": self.features,
            "limits": self.limits,
        }
