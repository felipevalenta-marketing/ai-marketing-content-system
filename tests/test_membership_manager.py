from __future__ import annotations

from pathlib import Path

from src.organizations.organization_manager import OrganizationManager
from src.users.user_manager import UserManager


def test_membership_manager_add_duplicate_and_owner_protection(tmp_path: Path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner@example.com", "hash", "Owner", role="admin")["user"]
    member = users.create_user("member@example.com", "hash", "Member")["user"]
    organization_manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)
    organization = organization_manager.create_organization({"name": "Acme Studio", "slug": "acme-studio"}, actor=owner)["data"]
    memberships = organization_manager.membership_manager

    owner_memberships = memberships.list_members(organization["organization_id"])["data"]["memberships"]
    owner_membership_id = next(item["membership_id"] for item in owner_memberships if item["role"] == "owner")

    owner_removal = memberships.remove_member(owner_membership_id, actor=owner)
    assert owner_removal["success"] is False
    assert any("owner" in error.lower() for error in owner_removal["errors"])

    added = memberships.add_member(organization["organization_id"], member["user_id"], role="member", actor=owner)
    assert added["success"] is True

    duplicate = memberships.add_member(organization["organization_id"], member["user_id"], role="member", actor=owner)
    assert duplicate["success"] is False
    assert any("exists" in error.lower() for error in duplicate["errors"])

    listed = memberships.list_user_memberships(member["user_id"])
    assert listed["success"] is True
    assert listed["data"]["count"] == 1


def test_membership_manager_updates_roles_safely(tmp_path: Path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner@example.com", "hash", "Owner", role="admin")["user"]
    member = users.create_user("member@example.com", "hash", "Member")["user"]
    organization_manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)
    organization = organization_manager.create_organization({"name": "Acme Studio", "slug": "acme-studio"}, actor=owner)["data"]
    memberships = organization_manager.membership_manager

    added = memberships.add_member(organization["organization_id"], member["user_id"], role="member", actor=owner)["data"]
    updated = memberships.update_member_role(added["membership_id"], "manager", actor=owner)
    assert updated["success"] is True
    assert updated["data"]["role"] == "manager"
