from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.organizations.organization_manager import OrganizationManager
from src.storage.storage_manager import StorageManager
from src.users.user_manager import UserManager


def test_organization_manager_create_list_profile_and_storage_context(tmp_path: Path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner@example.com", "hash", "Owner", role="admin")["user"]
    manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)

    created = manager.create_organization(
        {
            "name": "Acme Studio",
            "slug": "acme-studio",
            "settings": {"default_brand": "wenzel_partner"},
        },
        actor=owner,
    )

    assert created["success"] is True
    profile = created["data"]
    assert profile["organization_id"]
    assert profile["owner_user_id"] == owner["user_id"]
    assert profile["status"] == "active"
    assert profile["metadata"]["configuration_present"] is True

    listed = manager.list_organizations(user_id=owner["user_id"])
    assert listed["success"] is True
    assert listed["data"]["count"] == 1
    assert listed["data"]["organizations"][0]["organization_id"] == profile["organization_id"]
    assert manager.can_user_access_organization(owner["user_id"], profile["organization_id"]) is True
    assert profile["health_score"] >= 0
    assert profile["health_status"] in {"healthy", "warning", "critical"}
    assert profile["tenant_ready"] is True
    assert profile["analytics"]["member_count"] >= 1
    assert profile["metadata"]["tenant_ready"] is True
    assert profile["metadata"]["configuration_present"] is True
    assert "role_bridge" in profile

    storage = StorageManager(storage_root=tmp_path / "storage")
    saved = storage.save_generation(
        {
            "record_type": "generation",
            "record_id": "generation_org_context",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "organization_id": profile["organization_id"],
            "team_id": "team_demo",
            "payload": {"title": "Acme Studio"},
        }
    )
    assert saved["success"] is True
    listed = storage.list_records("generation")
    assert len(listed) == 1
    assert listed[0]["organization_id"] == profile["organization_id"]
    assert listed[0]["team_id"] == "team_demo"

    context = manager.get_organization_context(profile["organization_id"], user=owner)
    assert context["tenant_ready"] is True
    assert context["organization_id"] == profile["organization_id"]
    assert context["validation"]["valid"] is True
    assert context["role_bridge"]["owner"] == "admin"

    health = manager.get_organization_health(profile["organization_id"])
    assert health["health_score"] >= 0
    assert health["health_status"] in {"healthy", "warning", "critical"}


def test_organization_manager_rejects_duplicate_slug(tmp_path: Path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner2@example.com", "hash", "Owner", role="admin")["user"]
    manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)

    first = manager.create_organization({"name": "Acme Studio", "slug": "acme-studio"}, actor=owner)
    second = manager.create_organization({"name": "Another", "slug": "acme-studio"}, actor=owner)

    assert first["success"] is True
    assert second["success"] is False
    assert any("slug" in error.lower() for error in second["errors"])
