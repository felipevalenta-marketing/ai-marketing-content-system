"""Core authentication orchestration."""

from __future__ import annotations

from typing import Any

from src.auth.auth_result import build_failure_result, build_success_result
from src.auth.auth_validator import validate_jwt, validate_login_request, validate_registration_request
from src.auth.jwt_manager import create_access_token
from src.auth.password_manager import hash_password, verify_password
from src.users.user_manager import UserManager
from src.users.user_profile import build_safe_user_profile
from src.users.user_validator import normalize_email


class AuthManager:
    def __init__(self, user_manager: UserManager, jwt_secret: str = "", jwt_expiration_hours: int = 24, logger: Any | None = None) -> None:
        self.user_manager = user_manager
        self.jwt_secret = str(jwt_secret or "").strip()
        self.jwt_expiration_hours = int(jwt_expiration_hours or 24)
        self.logger = logger
        self.revoked_tokens: set[str] = set()

    def register(self, email: str, password: str, display_name: str) -> dict[str, Any]:
        if not self.jwt_secret:
            return build_failure_result("JWT secret is not configured.", warnings=["Authentication token unavailable."], metadata={"validation": {"valid": False, "warnings": [], "errors": ["JWT secret is not configured."]}})
        duplicate_user = self.user_manager.get_user_by_email(email) is not None
        validation = validate_registration_request(email, password, duplicate_user=duplicate_user)
        if not validation["valid"]:
            message = validation["errors"][0] if validation["errors"] else "Registration failed."
            return build_failure_result(message, warnings=validation["warnings"], metadata={"validation": validation})
        password_hash = hash_password(password)
        created = self.user_manager.create_user(email, password_hash, display_name, metadata={"created_by": "auth"}, created_by="auth")
        if not created.get("success"):
            return build_failure_result("Unable to create user.", warnings=created.get("warnings", []), metadata={"validation": validation})
        user = created.get("user", {})
        access_token = create_access_token({"sub": user.get("user_id", ""), "email": normalize_email(email)}, expires_in_hours=self.jwt_expiration_hours, secret=self.jwt_secret)
        if not access_token:
            return build_failure_result("JWT secret is not configured.", user=user, warnings=["Authentication token unavailable."], metadata={"validation": validation})
        return build_success_result(user=user, access_token=access_token, token_type="bearer", warnings=validation["warnings"], metadata={"validation": validation})

    def login(self, email: str, password: str) -> dict[str, Any]:
        if not self.jwt_secret:
            return build_failure_result("JWT secret is not configured.", warnings=["Authentication token unavailable."], metadata={"validation": {"valid": False, "warnings": [], "errors": ["JWT secret is not configured."]}})
        validation = validate_login_request(email, password)
        if not validation["valid"]:
            message = validation["errors"][0] if validation["errors"] else "Login failed."
            return build_failure_result(message, warnings=validation["warnings"], metadata={"validation": validation})
        user_record = self.user_manager.get_user_record_by_email(email)
        if not user_record or user_record.get("status") != "active":
            return build_failure_result("Invalid credentials.", warnings=[], metadata={"validation": validation})
        if not verify_password(password, user_record.get("password_hash", "")):
            return build_failure_result("Invalid credentials.", warnings=[], metadata={"validation": validation})
        user = build_safe_user_profile(user_record)
        access_token = create_access_token({"sub": user.get("user_id", ""), "email": normalize_email(email)}, expires_in_hours=self.jwt_expiration_hours, secret=self.jwt_secret)
        if not access_token:
            return build_failure_result("JWT secret is not configured.", user=user, warnings=["Authentication token unavailable."], metadata={"validation": validation})
        return build_success_result(user=user, access_token=access_token, token_type="bearer", warnings=[], metadata={"validation": validation})

    def logout(self, token: str) -> dict[str, Any]:
        normalized = str(token or "").strip()
        if normalized:
            self.revoked_tokens.add(normalized)
        return build_success_result(user={}, access_token="", token_type="bearer", warnings=["Session token discarded on the client."], metadata={"revoked": bool(normalized)})

    def authenticate(self, token: str) -> dict[str, Any]:
        normalized = str(token or "").strip()
        if not normalized:
            return build_failure_result("Authentication token is required.")
        if normalized in self.revoked_tokens:
            return build_failure_result("Token has been revoked.")
        validation = validate_jwt(normalized, secret=self.jwt_secret)
        if not validation["valid"]:
            return build_failure_result("Invalid or expired token.", warnings=validation["warnings"], metadata={"validation": validation})
        payload = validation.get("payload", {})
        user_id = payload.get("sub", "")
        user = self.user_manager.get_user(user_id) or self.user_manager.get_user_record(user_id)
        if not user:
            return build_failure_result("User not found.", metadata={"validation": validation})
        if str(user.get("status", "")).lower() != "active":
            return build_failure_result("User is not active.", user=user, metadata={"validation": validation})
        return build_success_result(user=user, access_token="", token_type="bearer", warnings=[], metadata={"validation": validation})

    def get_current_user(self, token: str) -> dict[str, Any]:
        result = self.authenticate(token)
        if not result.get("success"):
            return result
        return result


class AuthService:
    def __init__(self, manager: AuthManager) -> None:
        self.manager = manager

    def register(self, email: str, password: str, display_name: str) -> dict[str, Any]:
        return self.manager.register(email, password, display_name)

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self.manager.login(email, password)

    def logout(self, token: str) -> dict[str, Any]:
        return self.manager.logout(token)

    def authenticate(self, token: str) -> dict[str, Any]:
        return self.manager.authenticate(token)

    def get_current_user(self, token: str) -> dict[str, Any]:
        return self.manager.get_current_user(token)
