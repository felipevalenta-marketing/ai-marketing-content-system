from __future__ import annotations

from src.organizations.organization_context import build_context, get_membership_role_bridge, validate_context
from src.organizations.organization_manager import OrganizationManager
from src.users.user_manager import UserManager


def test_organization_context_builds_and_validates(tmp_path) -> None:
    users = UserManager(storage_path=tmp_path / "users")
    owner = users.create_user("owner@example.com", "hash", "Owner", role="admin")["user"]
    manager = OrganizationManager(storage_root=str(tmp_path / "organizations"), users=users)
    created = manager.create_organization({"name": "Acme Studio", "slug": "acme-studio"}, actor=owner)
    organization_id = created["data"]["organization_id"]

    context = build_context(manager, user=owner, organization_id=organization_id)

    assert context["organization_id"] == organization_id
    assert context["tenant_ready"] is True
    assert context["role_bridge"]["owner"] == "admin"
    assert validate_context(context)["valid"] is True
    assert get_membership_role_bridge()["member"] == "editor"

