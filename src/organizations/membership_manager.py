"""Membership management."""

from __future__ import annotations

from typing import Any
import uuid

from src.reporting.report_metrics import safe_dict, safe_text, utc_now_iso
from src.users.user_manager import UserManager

from .organization_result import build_organization_failure, build_organization_success
from .organization_storage import ensure_organizations_root, load_json, save_json
from .membership_contracts import MembershipContract
from .membership_validator import validate_membership
from .team_manager import TeamManager


ORG_ROLES = {"owner", "admin", "manager", "member", "viewer"}
TEAM_ROLES = {"lead", "editor", "member", "viewer"}


class MembershipManager:
    def __init__(self, storage_root: str = "data/organizations", users: UserManager | None = None, organization_manager: Any | None = None, team_manager: TeamManager | None = None, logger: Any | None = None) -> None:
        self.storage_root = ensure_organizations_root(storage_root)
        self.file_path = self.storage_root / "memberships.json"
        self.users = users or UserManager()
        self.organization_manager = organization_manager
        self.team_manager = team_manager or TeamManager(storage_root=storage_root, organization_manager=organization_manager)
        self.logger = logger
        if not self.file_path.exists():
            save_json(self.file_path, {"memberships": []})

    def add_member(self, organization_id: str, user_id: str, role: str = "member", team_id: str | None = None, actor: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._organization_exists(organization_id):
            return build_organization_failure("Organization not found.")
        if not self._user_exists(user_id):
            return build_organization_failure("User not found.")
        if team_id and not self._team_exists(team_id):
            return build_organization_failure("Team not found.")
        role = safe_text(role, limit=40).lower() or "member"
        if role not in ORG_ROLES and role not in TEAM_ROLES:
            return build_organization_failure("Invalid membership role.")
        store = load_json(self.file_path, {"memberships": []})
        memberships = store.setdefault("memberships", [])
        if any(str(item.get("organization_id", "")) == organization_id and str(item.get("user_id", "")) == user_id and str(item.get("team_id", "")) == str(team_id or "") for item in memberships):
            return build_organization_failure("Membership already exists.")
        membership = {
            "membership_id": safe_text(f"mbr_{uuid.uuid4().hex}", limit=120),
            "organization_id": safe_text(organization_id, limit=120),
            "team_id": safe_text(team_id or "", limit=120),
            "user_id": safe_text(user_id, limit=120),
            "role": role,
            "status": "active",
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "metadata": {"created_by": safe_text((actor or {}).get("user_id"), limit=120), "updated_by": safe_text((actor or {}).get("user_id"), limit=120)},
        }
        validation = validate_membership(membership, organization_exists=self._organization_exists(organization_id), team_exists=not team_id or self._team_exists(team_id), user_exists=True, existing_memberships=memberships)
        if not validation["valid"]:
            return build_organization_failure(validation["errors"][0] if validation["errors"] else "Invalid membership.", warnings=validation["warnings"], metadata={"validation": validation})
        memberships.append(membership)
        save_json(self.file_path, store)
        return build_organization_success(data=MembershipContract(**membership).to_dict(), metadata={"validation": validation})

    def remove_member(self, membership_id: str, actor: dict[str, Any] | None = None) -> dict[str, Any]:
        store = load_json(self.file_path, {"memberships": []})
        memberships = store.get("memberships", [])
        target = next((item for item in memberships if str(item.get("membership_id", "")) == str(membership_id)), None)
        if not target:
            return build_organization_failure("Membership not found.")
        if str(target.get("role", "")).lower() == "owner":
            owners = [item for item in memberships if str(item.get("organization_id", "")) == str(target.get("organization_id", "")) and str(item.get("role", "")).lower() == "owner" and str(item.get("membership_id", "")) != membership_id]
            if not owners:
                return build_organization_failure("Cannot remove the only owner.")
        store["memberships"] = [item for item in memberships if str(item.get("membership_id", "")) != str(membership_id)]
        save_json(self.file_path, store)
        return build_organization_success(data={"removed": True}, metadata={"membership_id": membership_id})

    def list_members(self, organization_id: str) -> dict[str, Any]:
        memberships = [dict(item) for item in load_json(self.file_path, {"memberships": []}).get("memberships", []) if str(item.get("organization_id", "")) == str(organization_id)]
        return build_organization_success(data={"memberships": memberships, "count": len(memberships)}, metadata={"organization_id": organization_id})

    def list_user_memberships(self, user_id: str) -> dict[str, Any]:
        memberships = [dict(item) for item in load_json(self.file_path, {"memberships": []}).get("memberships", []) if str(item.get("user_id", "")) == str(user_id)]
        return build_organization_success(data={"memberships": memberships, "count": len(memberships)}, metadata={"user_id": user_id})

    def update_member_role(self, membership_id: str, role: str, actor: dict[str, Any] | None = None) -> dict[str, Any]:
        role = safe_text(role, limit=40).lower()
        if role not in ORG_ROLES and role not in TEAM_ROLES:
            return build_organization_failure("Invalid membership role.")
        store = load_json(self.file_path, {"memberships": []})
        memberships = store.get("memberships", [])
        for index, membership in enumerate(memberships):
            if str(membership.get("membership_id", "")) != str(membership_id):
                continue
            membership["role"] = role
            membership["updated_at"] = utc_now_iso()
            membership["metadata"] = {**safe_dict(membership.get("metadata")), "updated_by": safe_text((actor or {}).get("user_id"), limit=120)}
            memberships[index] = membership
            save_json(self.file_path, store)
            return build_organization_success(data=MembershipContract(**membership).to_dict(), metadata={"membership_id": membership_id})
        return build_organization_failure("Membership not found.")

    def is_member(self, user_id: str, organization_id: str) -> bool:
        memberships = load_json(self.file_path, {"memberships": []}).get("memberships", [])
        return any(str(item.get("user_id", "")) == str(user_id) and str(item.get("organization_id", "")) == str(organization_id) for item in memberships)

    def _organization_exists(self, organization_id: str) -> bool:
        if self.organization_manager is None:
            return True
        return bool(self.organization_manager.get_organization(organization_id))

    def _team_exists(self, team_id: str) -> bool:
        return bool(self.team_manager.get_team(team_id))

    def _user_exists(self, user_id: str) -> bool:
        return bool(self.users.get_user_record(user_id) or self.users.get_user(user_id))

