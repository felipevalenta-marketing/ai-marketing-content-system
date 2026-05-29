"""Team management."""

from __future__ import annotations

from typing import Any
import uuid

from src.reporting.report_metrics import safe_dict, safe_text, utc_now_iso

from .organization_result import build_organization_failure, build_organization_success
from .organization_storage import ensure_organizations_root, load_json, save_json
from .organization_registry import normalize_slug
from .team_contracts import TeamContract
from .team_validator import validate_team


class TeamManager:
    def __init__(self, storage_root: str = "data/organizations", organization_manager: Any | None = None, logger: Any | None = None) -> None:
        self.storage_root = ensure_organizations_root(storage_root)
        self.file_path = self.storage_root / "teams.json"
        self.organization_manager = organization_manager
        self.logger = logger
        if not self.file_path.exists():
            save_json(self.file_path, {"teams": []})

    def create_team(self, organization_id: str, data: dict[str, Any], actor: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._organization_exists(organization_id):
            return build_organization_failure("Organization not found.")
        name = safe_text(data.get("name"), limit=160)
        if not name:
            return build_organization_failure("Team name is required.")
        team = {
            "team_id": safe_text(data.get("team_id") or f"team_{uuid.uuid4().hex}", limit=120),
            "organization_id": safe_text(organization_id, limit=120),
            "name": name,
            "slug": normalize_slug(data.get("slug") or name),
            "status": safe_text(data.get("status") or "active", limit=40),
            "created_at": utc_now_iso(),
            "updated_at": utc_now_iso(),
            "metadata": {
                **safe_dict(data.get("metadata")),
                "created_by": safe_text((actor or {}).get("user_id"), limit=120),
                "updated_by": safe_text((actor or {}).get("user_id"), limit=120),
            },
        }
        validation = validate_team(team, organization_exists=True)
        if not validation["valid"]:
            return build_organization_failure(validation["errors"][0] if validation["errors"] else "Invalid team.", warnings=validation["warnings"], metadata={"validation": validation})
        store = load_json(self.file_path, {"teams": []})
        if any(str(item.get("organization_id", "")) == organization_id and str(item.get("slug", "")) == team["slug"] for item in store.get("teams", [])):
            return build_organization_failure("Team slug already exists in organization.")
        store.setdefault("teams", []).append(team)
        save_json(self.file_path, store)
        return build_organization_success(data=TeamContract(**team).to_dict(), metadata={"team_id": team["team_id"], "organization_id": organization_id, "validation": validation})

    def get_team(self, team_id: str) -> dict[str, Any]:
        for team in load_json(self.file_path, {"teams": []}).get("teams", []):
            if str(team.get("team_id", "")) == str(team_id):
                return dict(team)
        return {}

    def list_teams(self, organization_id: str) -> dict[str, Any]:
        teams = [dict(item) for item in load_json(self.file_path, {"teams": []}).get("teams", []) if str(item.get("organization_id", "")) == str(organization_id)]
        return build_organization_success(data={"teams": teams, "count": len(teams)}, metadata={"organization_id": organization_id})

    def update_team(self, team_id: str, data: dict[str, Any], actor: dict[str, Any] | None = None) -> dict[str, Any]:
        store = load_json(self.file_path, {"teams": []})
        teams = store.get("teams", [])
        for index, team in enumerate(teams):
            if str(team.get("team_id", "")) != str(team_id):
                continue
            if "name" in data and data["name"]:
                team["name"] = safe_text(data["name"], limit=160)
            if "slug" in data and data["slug"]:
                team["slug"] = normalize_slug(data["slug"])
            if "status" in data and safe_text(data["status"], limit=40) in {"active", "inactive", "archived"}:
                team["status"] = safe_text(data["status"], limit=40)
            team["metadata"] = {**safe_dict(team.get("metadata")), **safe_dict(data.get("metadata")), "updated_by": safe_text((actor or {}).get("user_id"), limit=120)}
            team["updated_at"] = utc_now_iso()
            teams[index] = team
            save_json(self.file_path, store)
            return build_organization_success(data=TeamContract(**team).to_dict(), metadata={"team_id": team_id})
        return build_organization_failure("Team not found.")

    def archive_team(self, team_id: str, actor: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.update_team(team_id, {"status": "archived"}, actor=actor)

    def _organization_exists(self, organization_id: str) -> bool:
        if self.organization_manager is None:
            return True
        return bool(self.organization_manager.get_organization(organization_id))

