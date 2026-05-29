from __future__ import annotations

from src.rbac.permission_checker import check_permission


def test_permission_checker_admin_and_viewer_rules() -> None:
    admin = {"role": "admin"}
    viewer = {"role": "viewer"}
    editor = {"role": "editor"}
    manager = {"role": "manager"}
    disabled = {"role": "disabled"}

    assert check_permission(admin, "generation:create")["allowed"] is True
    assert check_permission(viewer, "generation:create")["allowed"] is False
    assert check_permission(editor, "generation:create")["allowed"] is True
    assert check_permission(manager, "workflow:run")["allowed"] is True
    assert check_permission(disabled, "analytics:read")["allowed"] is False
    assert check_permission({"role": "superuser"}, "analytics:read")["allowed"] is False
