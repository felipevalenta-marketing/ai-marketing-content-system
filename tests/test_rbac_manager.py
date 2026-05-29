from __future__ import annotations

from pathlib import Path

from src.rbac.rbac_manager import RBACManager
from src.users.user_manager import UserManager


def test_rbac_manager_role_assignment_and_summary(tmp_path: Path) -> None:
    users = UserManager(storage_path=str(tmp_path / "users"))
    rbac = RBACManager(users)

    admin = users.create_user("admin@example.com", "hash", "Admin")["user"]
    viewer = users.create_user("viewer@example.com", "hash", "Viewer")["user"]

    assert rbac.get_user_role(admin) == "admin"
    assert rbac.has_permission(admin, "admin:all") is True
    assert rbac.has_permission(viewer, "generation:create") is False

    summary = rbac.build_access_summary(admin)
    assert summary["role"] == "admin"
    assert summary["role_level"] == 100
    assert summary["role_type"] == "system"
    assert "admin:all" in summary["permissions"]
    assert summary["summary"]["can_manage_system"] is True
    assert summary["permission_domains"]

    health = rbac.get_health()
    assert health["status"] in {"healthy", "warning"}
    assert health["health_score"] <= 100

    assigned = rbac.assign_role(viewer["user_id"], "editor", actor=admin)
    assert assigned["success"] is True
    updated = users.get_user(viewer["user_id"])
    assert updated["role"] == "editor"
