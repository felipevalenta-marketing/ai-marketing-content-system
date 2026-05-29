"""Organization management."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid

from src.reporting.report_metrics import safe_dict, safe_int, safe_list, safe_text, utc_now_iso
from src.users.user_manager import UserManager

from .brand_access_manager import BrandAccessManager
from .organization_context import build_context, validate_context
from .membership_manager import MembershipManager
from .organization_contracts import OrganizationProfileContract
from .organization_registry import is_valid_organization_id, normalize_slug
from .organization_health import build_organization_health
from .organization_profile import build_organization_profile_payload
from .organization_result import build_organization_failure, build_organization_success
from .organization_settings import build_organization_settings
from .organization_storage import ensure_organizations_root, load_json, save_json
from .organization_validator import validate_organization


class OrganizationManager:
    def __init__(
        self,
        storage_root: str = "data/organizations",
        users: UserManager | None = None,
        settings: Any | None = None,
        brand_access_manager: BrandAccessManager | None = None,
        membership_manager: MembershipManager | None = None,
        logger: Any | None = None,
    ) -> None:
        self.storage_root = ensure_organizations_root(storage_root)
        self.file_path = self.storage_root / "organizations.json"
        self.users = users or UserManager()
        self.settings = settings
        self.logger = logger
        self.analytics_engine = None
        self.brand_access_manager = brand_access_manager or BrandAccessManager(storage_root=storage_root, organization_manager=self)
        self.membership_manager = membership_manager or MembershipManager(storage_root=storage_root, users=self.users, organization_manager=self)
        self.team_manager = getattr(self.membership_manager, "team_manager", None)
        if not self.file_path.exists():
            save_json(self.file_path, {"organizations": []})

    def create_organization(self, data: dict[str, Any], actor: dict[str, Any] | None = None) -> dict[str, Any]:
        name = safe_text(data.get("name"), limit=160)
        if not name:
            return build_organization_failure("Organization name is required.")
        slug = normalize_slug(data.get("slug") or name)
        organization = {
            "organization_id": safe_text(data.get("organization_id") or f"org_{uuid.uuid4().hex}", limit=120),
            "name": name,
            "slug": slug,
            "status": safe_text(data.get("status") or "active", limit=40),
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "owner_user_id": safe_text((actor or {}).get("user_id") or data.get("owner_user_id"), limit=120),
            "settings": build_organization_settings(safe_dict(data.get("settings")), config_summary=self._configuration_summary()),
            "metadata": {
                **safe_dict(data.get("metadata")),
                "created_by": safe_text((actor or {}).get("user_id") or data.get("owner_user_id"), limit=120),
                "updated_by": safe_text((actor or {}).get("user_id") or data.get("owner_user_id"), limit=120),
            },
        }
        validation = validate_organization(organization)
        if not validation["valid"]:
            return build_organization_failure(validation["errors"][0] if validation["errors"] else "Invalid organization.", warnings=validation["warnings"], metadata={"validation": validation})
        store = load_json(self.file_path, {"organizations": []})
        if any(str(item.get("slug", "")).strip() == slug for item in store.get("organizations", [])):
            return build_organization_failure("Organization slug already exists.")
        store.setdefault("organizations", []).append(organization)
        save_json(self.file_path, store)
        if organization["owner_user_id"]:
            self.membership_manager.add_member(organization["organization_id"], organization["owner_user_id"], role="owner", actor=actor)
        return build_organization_success(data=self.build_organization_profile(organization["organization_id"]), metadata={"organization_id": organization["organization_id"], "validation": validation})

    def get_organization(self, organization_id: str) -> dict[str, Any]:
        for organization in load_json(self.file_path, {"organizations": []}).get("organizations", []):
            if str(organization.get("organization_id", "")) == str(organization_id):
                return dict(organization)
        return {}

    def get_organization_by_slug(self, slug: str) -> dict[str, Any]:
        normalized = normalize_slug(slug)
        for organization in load_json(self.file_path, {"organizations": []}).get("organizations", []):
            if str(organization.get("slug", "")) == normalized:
                return dict(organization)
        return {}

    def list_organizations(self, user_id: str | None = None) -> dict[str, Any]:
        organizations = [dict(item) for item in load_json(self.file_path, {"organizations": []}).get("organizations", [])]
        if user_id:
            memberships = self.membership_manager.list_user_memberships(user_id)
            org_ids = {item.get("organization_id") for item in memberships.get("data", {}).get("memberships", [])}
            organizations = [item for item in organizations if item.get("organization_id") in org_ids or item.get("owner_user_id") == user_id]
        profiles = [self.build_organization_profile(item.get("organization_id", "")) for item in organizations]
        return build_organization_success(data={"organizations": profiles, "count": len(profiles)}, metadata={"user_id": user_id or ""})

    def update_organization(self, organization_id: str, data: dict[str, Any], actor: dict[str, Any] | None = None) -> dict[str, Any]:
        store = load_json(self.file_path, {"organizations": []})
        organizations = store.get("organizations", [])
        for index, organization in enumerate(organizations):
            if str(organization.get("organization_id", "")) != str(organization_id):
                continue
            if "name" in data and data["name"]:
                organization["name"] = safe_text(data["name"], limit=160)
            if "slug" in data and data["slug"]:
                organization["slug"] = normalize_slug(data["slug"])
            if "status" in data and safe_text(data["status"], limit=40) in {"active", "inactive", "suspended"}:
                organization["status"] = safe_text(data["status"], limit=40)
            if "settings" in data and isinstance(data["settings"], dict):
                organization["settings"] = build_organization_settings({**safe_dict(organization.get("settings")), **safe_dict(data.get("settings"))}, config_summary=self._configuration_summary())
            organization["metadata"] = {
                **safe_dict(organization.get("metadata")),
                **safe_dict(data.get("metadata")),
                "updated_by": safe_text((actor or {}).get("user_id", ""), limit=120),
            }
            organization["updated_at"] = utc_now_iso()
            organizations[index] = organization
            store["organizations"] = organizations
            save_json(self.file_path, store)
            return build_organization_success(data=self.build_organization_profile(organization_id), metadata={"organization_id": organization_id})
        return build_organization_failure("Organization not found.")

    def deactivate_organization(self, organization_id: str, actor: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.update_organization(organization_id, {"status": "inactive"}, actor=actor)

    def build_organization_profile(self, organization_id: str) -> dict[str, Any]:
        profile = build_organization_profile_payload(self, organization_id, analytics_metadata=self._organization_analytics_metadata(organization_id))
        if not profile:
            return {}
        organization = safe_dict(profile.get("organization"))
        organization_profile = OrganizationProfileContract(
            organization_id=organization.get("organization_id", ""),
            name=organization.get("name", ""),
            slug=organization.get("slug", ""),
            status=organization.get("status", "active"),
            created_at=organization.get("created_at", ""),
            updated_at=organization.get("updated_at", ""),
            owner_user_id=organization.get("owner_user_id", ""),
            settings=organization.get("settings", {}),
            metadata={
                **safe_dict(organization.get("metadata")),
                "created_at": organization.get("created_at", ""),
                "modified_at": organization.get("updated_at", ""),
                "file_count": self._organization_file_count(),
                "markdown_count": 0,
                "configuration_present": True,
                "tenant_ready": True,
            },
            team_count=safe_int(profile.get("team_count"), 0),
            member_count=safe_int(profile.get("member_count"), 0),
            brand_count=safe_int(profile.get("brand_count"), 0),
            active_brand_ids=[str(item.get("brand_id", "")) for item in safe_list(profile.get("brands")) if item.get("brand_id")],
            health_score=safe_int(profile.get("health_score"), 0),
            health_status=safe_text(profile.get("health_status"), limit=40) or "warning",
            warnings=safe_list(profile.get("warnings")),
            teams=safe_list(profile.get("teams")),
            members=safe_list(profile.get("members")),
            brands=safe_list(profile.get("brands")),
            health=safe_dict(profile.get("health")),
            organization=organization,
            tenant_ready=True,
            tenant_configuration=safe_dict(profile.get("tenant_configuration")),
            tenant_limits=safe_dict(profile.get("tenant_limits")),
            analytics=safe_dict(profile.get("analytics")),
            role_bridge=safe_dict(profile.get("role_bridge")),
        )
        payload = organization_profile.to_dict()
        payload.update(profile)
        return payload

    def can_user_access_organization(self, user_id: str, organization_id: str, team_id: str | None = None) -> bool:
        if not user_id or not organization_id:
            return False
        if not self.membership_manager.is_member(user_id, organization_id):
            return False
        if not team_id:
            return True
        memberships = self.membership_manager.list_user_memberships(user_id).get("data", {}).get("memberships", [])
        return any(str(item.get("organization_id", "")) == str(organization_id) and str(item.get("team_id", "")) == str(team_id) for item in memberships)

    def get_organization_health(self, organization_id: str) -> dict[str, Any]:
        profile = self.build_organization_profile(organization_id)
        if not profile:
            return {}
        return safe_dict(profile.get("health"))

    def get_organization_context(self, organization_id: str, team_id: str | None = None, brand_id: str | None = None, user: dict[str, Any] | None = None) -> dict[str, Any]:
        context = build_context(self, user=user, organization_id=organization_id, team_id=team_id, brand_id=brand_id)
        context["health"] = self.get_organization_health(organization_id)
        context["validation"] = validate_context(context)
        return context

    def _configuration_summary(self) -> dict[str, Any]:
        settings = self.settings
        if settings is None:
            return {}
        getter = getattr(settings, "get_system_summary", None)
        if callable(getter):
            try:
                return safe_dict(getter())
            except Exception:
                return {}
        return {}

    def _organization_file_count(self) -> int:
        try:
            return sum(1 for item in self.storage_root.iterdir() if item.is_file() and item.suffix.lower() in {".json", ".md", ".txt"})
        except Exception:
            return 0

    def _organization_analytics_metadata(self, organization_id: str) -> dict[str, Any]:
        analytics_engine = getattr(self, "analytics_engine", None)
        if analytics_engine is None:
            return {"workflow_count": 0, "report_count": 0, "token_usage": {}, "estimated_cost": {}}
        try:
            response = analytics_engine.generate_analytics(
                {
                    "analytics_type": "executive_dashboard",
                    "organization_id": organization_id,
                    "include_storage": True,
                    "include_tokens": True,
                    "include_costs": True,
                    "include_governance": True,
                    "include_reports": True,
                    "filters": {"organization_id": organization_id},
                }
            )
        except Exception:
            return {"workflow_count": 0, "report_count": 0, "token_usage": {}, "estimated_cost": {}}
        kpis = safe_dict(response.get("kpis"))
        sections = safe_dict(response.get("sections"))
        executive = safe_dict(kpis.get("executive"))
        token_section = safe_dict(sections.get("token"))
        cost_section = safe_dict(sections.get("cost"))
        return {
            "workflow_count": safe_int(safe_dict(sections.get("workflow")).get("workflows", {}).get("total_workflows"), safe_int(executive.get("total_workflows", {}).get("value"), 0)),
            "report_count": safe_int(safe_dict(sections.get("report")).get("reports", {}).get("total_reports"), safe_int(executive.get("total_reports", {}).get("value"), 0)),
            "token_usage": safe_dict(token_section.get("usage")) or safe_dict(executive.get("total_tokens")),
            "estimated_cost": safe_dict(cost_section.get("usage")) or safe_dict(executive.get("total_cost")),
        }
