from __future__ import annotations

from pathlib import Path

from src.users.user_manager import UserManager


def test_user_manager_create_update_and_list(tmp_path: Path) -> None:
    manager = UserManager(storage_path=str(tmp_path / "users"))
    created = manager.create_user("User@Example.com", "hashed", "Test User")
    assert created["success"] is True
    user_id = created["user"]["user_id"]
    assert created["user"]["role"] == "admin"
    assert manager.get_user_by_email("user@example.com")["email"] == "user@example.com"

    updated = manager.update_user(user_id, {"display_name": "Updated User", "settings": {"theme": "dark"}})
    assert updated["success"] is True
    assert updated["user"]["display_name"] == "Updated User"

    users = manager.list_users()
    assert len(users) == 1
    assert "password_hash" not in users[0]


def test_user_manager_deactivate_user(tmp_path: Path) -> None:
    manager = UserManager(storage_path=str(tmp_path / "users"))
    created = manager.create_user("user2@example.com", "hashed", "User Two")
    user_id = created["user"]["user_id"]
    deactivated = manager.deactivate_user(user_id)
    assert deactivated["success"] is True
    assert deactivated["user"]["status"] == "inactive"
