from __future__ import annotations

from src.rbac.role_registry import get_role, get_role_hierarchy, is_valid_role, list_roles, role_has_at_least


def test_role_registry_includes_default_roles() -> None:
    roles = list_roles()
    role_names = {str(role.get("role")) for role in roles}

    assert {"admin", "manager", "editor", "viewer", "disabled"}.issubset(role_names)
    assert is_valid_role("viewer") is True
    assert get_role("admin")["level"] == 100
    assert get_role("admin")["type"] == "system"
    assert get_role("admin")["inherits_from"] == ["manager"]
    assert role_has_at_least("admin", "manager") is True
    assert role_has_at_least("viewer", "manager") is False
    assert get_role_hierarchy()[0]["role"] == "admin"
