from __future__ import annotations

from src.rbac.permission_registry import get_permission, is_valid_permission, list_permission_domains, list_permissions, permissions_by_domain


def test_permission_registry_includes_core_permissions() -> None:
    permissions = list_permissions()
    permission_names = {str(permission.get("permission")) for permission in permissions}

    assert "workflow:run" in permission_names
    assert "admin:all" in permission_names
    assert is_valid_permission("report:create") is True
    assert get_permission("analytics:read")["domain"] == "analytics"
    assert "workflow" in permissions_by_domain()
    assert any(domain.get("domain") == "system" for domain in list_permission_domains())
