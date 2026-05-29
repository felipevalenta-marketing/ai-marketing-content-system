"""Local file-backed user storage."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import tempfile
import uuid

from src.reporting.report_metrics import safe_dict, safe_list, safe_text, utc_now_iso
from src.users.user_profile import build_safe_user_profile
from src.users.user_validator import normalize_email, validate_email, validate_user_status
from src.rbac.role_registry import normalize_role_name, is_valid_role


class UserManager:
    def __init__(self, storage_path: str = "data/users", logger: Any | None = None, default_role: str = "viewer", first_user_admin: bool = True) -> None:
        self.storage_path = Path(storage_path)
        self.logger = logger
        self.default_role = normalize_role_name(default_role) or "viewer"
        self.first_user_admin = bool(first_user_admin)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.file_path = self.storage_path / "users.json"
        if not self.file_path.exists():
            self._save({"users": []})

    def create_user(self, email: str, password_hash: str, display_name: str, settings: dict[str, Any] | None = None, metadata: dict[str, Any] | None = None, status: str = "active", created_by: str | None = None, role: str | None = None) -> dict[str, Any]:
        normalized_email = normalize_email(email)
        validation = validate_email(normalized_email)
        if not validation["valid"]:
            return {"success": False, "user": {}, "warnings": [], "errors": validation["errors"], "metadata": {}}
        if self.get_user_by_email(normalized_email):
            return {"success": False, "user": {}, "warnings": [], "errors": ["Email already exists."], "metadata": {}}
        status_validation = validate_user_status(status)
        if not status_validation["valid"]:
            return {"success": False, "user": {}, "warnings": [], "errors": status_validation["errors"], "metadata": {}}
        now = utc_now_iso()
        existing_users = self._load().get("users", [])
        assigned_role = normalize_role_name(role or "")
        if not assigned_role:
            assigned_role = "admin" if self.first_user_admin and not existing_users else self.default_role
        if not is_valid_role(assigned_role):
            assigned_role = self.default_role
        user = {
            "user_id": f"usr_{uuid.uuid4().hex}",
            "email": normalized_email,
            "display_name": safe_text(display_name or normalized_email.split("@", 1)[0], limit=120),
            "status": str(status or "active").strip().lower() or "active",
            "role": assigned_role,
            "permissions": [],
            "created_at": now,
            "updated_at": now,
            "password_hash": safe_text(password_hash, limit=512),
            "settings": safe_dict(settings),
            "metadata": {
                **safe_dict(metadata),
                "created_by": created_by or "self",
                "updated_by": created_by or "self",
            },
        }
        store = self._load()
        store.setdefault("users", []).append(user)
        self._save(store)
        return {"success": True, "user": build_safe_user_profile(user), "warnings": [], "errors": [], "metadata": {"user_id": user["user_id"]}}

    def get_user(self, user_id: str) -> dict[str, Any] | None:
        for user in self._load().get("users", []):
            if user.get("user_id") == user_id:
                return build_safe_user_profile(user)
        return None

    def get_user_record(self, user_id: str) -> dict[str, Any] | None:
        for user in self._load().get("users", []):
            if user.get("user_id") == user_id:
                return dict(user)
        return None

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        normalized_email = normalize_email(email)
        for user in self._load().get("users", []):
            if normalize_email(user.get("email", "")) == normalized_email:
                return build_safe_user_profile(user)
        return None

    def get_user_record_by_email(self, email: str) -> dict[str, Any] | None:
        normalized_email = normalize_email(email)
        for user in self._load().get("users", []):
            if normalize_email(user.get("email", "")) == normalized_email:
                return dict(user)
        return None

    def update_user(self, user_id: str, updates: dict[str, Any], updated_by: str | None = None, allow_role: bool = False) -> dict[str, Any]:
        store = self._load()
        users = store.get("users", [])
        for index, user in enumerate(users):
            if user.get("user_id") != user_id:
                continue
            if "email" in updates:
                normalized_email = normalize_email(updates.get("email", ""))
                if normalized_email and normalized_email != normalize_email(user.get("email", "")):
                    if self.get_user_by_email(normalized_email):
                        return {"success": False, "user": {}, "warnings": [], "errors": ["Email already exists."], "metadata": {}}
                    user["email"] = normalized_email
            if "display_name" in updates and updates["display_name"] is not None:
                user["display_name"] = safe_text(updates["display_name"], limit=120)
            if "settings" in updates and isinstance(updates["settings"], dict):
                user["settings"] = safe_dict(updates["settings"])
            if "status" in updates:
                status_validation = validate_user_status(updates.get("status"))
                if not status_validation["valid"]:
                    return {"success": False, "user": {}, "warnings": [], "errors": status_validation["errors"], "metadata": {}}
                user["status"] = str(updates.get("status")).strip().lower()
            if allow_role and "role" in updates:
                candidate_role = normalize_role_name(updates.get("role"))
                if is_valid_role(candidate_role):
                    user["role"] = candidate_role
            metadata = safe_dict(user.get("metadata"))
            metadata["updated_by"] = updated_by or user_id
            user["metadata"] = metadata
            user["updated_at"] = utc_now_iso()
            users[index] = user
            store["users"] = users
            self._save(store)
            return {"success": True, "user": build_safe_user_profile(user), "warnings": [], "errors": [], "metadata": {"user_id": user_id}}
        return {"success": False, "user": {}, "warnings": [], "errors": ["User not found."], "metadata": {}}

    def deactivate_user(self, user_id: str) -> dict[str, Any]:
        return self.update_user(user_id, {"status": "inactive"}, updated_by=user_id)

    def list_users(self) -> list[dict[str, Any]]:
        return [build_safe_user_profile(user) for user in self._load().get("users", [])]

    def _load(self) -> dict[str, Any]:
        if not self.file_path.exists():
            return {"users": []}
        try:
            raw = self.file_path.read_text(encoding="utf-8")
            payload = json.loads(raw) if raw.strip() else {"users": []}
            if isinstance(payload, dict) and isinstance(payload.get("users"), list):
                return payload
        except Exception:
            pass
        return {"users": []}

    def _save(self, payload: dict[str, Any]) -> None:
        self.storage_path.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix="users_", suffix=".json", dir=str(self.storage_path))
        temp_file = Path(temp_path)
        try:
            with open(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
            temp_file.replace(self.file_path)
        finally:
            if temp_file.exists() and temp_file != self.file_path:
                try:
                    temp_file.unlink()
                except Exception:
                    pass
