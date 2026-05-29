from __future__ import annotations

from pathlib import Path

from src.organizations.organization_manager import OrganizationManager
from src.users.user_manager import UserManager


def test_team_manager_create_list_update_and_archive(tmp_path: Path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner@example.com", "hash", "Owner", role="admin")["user"]
    organization_manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)
    organization = organization_manager.create_organization({"name": "Acme Studio", "slug": "acme-studio"}, actor=owner)["data"]
    team_manager = organization_manager.membership_manager.team_manager

    created = team_manager.create_team(
        organization["organization_id"],
        {"name": "Creative Team", "slug": "creative-team"},
        actor=owner,
    )
    assert created["success"] is True
    team = created["data"]
    assert team["organization_id"] == organization["organization_id"]
    assert team["status"] == "active"

    listed = team_manager.list_teams(organization["organization_id"])
    assert listed["success"] is True
    assert listed["data"]["count"] == 1

    updated = team_manager.update_team(team["team_id"], {"name": "Creative Ops"}, actor=owner)
    assert updated["success"] is True
    assert updated["data"]["name"] == "Creative Ops"

    archived = team_manager.archive_team(team["team_id"], actor=owner)
    assert archived["success"] is True
    assert archived["data"]["status"] == "archived"


def test_team_manager_rejects_missing_organization(tmp_path: Path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner@example.com", "hash", "Owner", role="admin")["user"]
    organization_manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)
    team_manager = organization_manager.membership_manager.team_manager

    created = team_manager.create_team("missing-org", {"name": "Creative Team", "slug": "creative-team"}, actor=owner)
    assert created["success"] is False
    assert any("organization" in error.lower() for error in created["errors"])
