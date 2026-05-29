from __future__ import annotations

from pathlib import Path

from src.organizations.organization_manager import OrganizationManager
from src.users.user_manager import UserManager


def test_brand_access_manager_grant_list_revoke_and_validate(tmp_path: Path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner@example.com", "hash", "Owner", role="admin")["user"]
    organization_manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)
    organization = organization_manager.create_organization({"name": "Acme Studio", "slug": "acme-studio"}, actor=owner)["data"]
    brand_access = organization_manager.brand_access_manager

    granted = brand_access.grant_brand_access(organization["organization_id"], "wenzel_partner", access_level="manage", actor=owner)
    assert granted["success"] is True
    assert granted["data"]["brand_id"] == "wenzel_partner"
    assert granted["data"]["access_level"] == "manage"
    assert brand_access.can_access_brand(organization["organization_id"], "wenzel_partner", "use") is True

    listed = brand_access.list_organization_brands(organization["organization_id"])
    assert listed["success"] is True
    assert listed["data"]["count"] == 1

    revoked = brand_access.revoke_brand_access(organization["organization_id"], "wenzel_partner", actor=owner)
    assert revoked["success"] is True
    assert revoked["data"]["removed"] == 1
    assert brand_access.can_access_brand(organization["organization_id"], "wenzel_partner", "use") is False


def test_brand_access_manager_rejects_missing_organization(tmp_path: Path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner@example.com", "hash", "Owner", role="admin")["user"]
    organization_manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)
    brand_access = organization_manager.brand_access_manager

    result = brand_access.grant_brand_access("missing-org", "wenzel_partner", actor=owner)
    assert result["success"] is False
    assert any("organization" in error.lower() for error in result["errors"])
