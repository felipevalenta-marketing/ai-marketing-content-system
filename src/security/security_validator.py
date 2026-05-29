"""Security validation orchestration."""

from __future__ import annotations

from typing import Any
import os

from src.security.auth_security import build_auth_security_summary
from src.security.dependency_validator import validate_dependencies
from src.security.input_sanitizer import validate_input
from src.security.output_sanitizer import validate_output
from src.auth.jwt_manager import create_access_token
from src.security.path_security import validate_path
from src.security.rbac_security import build_rbac_security_summary
from src.security.security_policy import build_security_policy
from src.security.secret_scanner import scan_repository
from src.security.security_config import build_security_configuration


def validate_security(app: Any | None = None) -> dict[str, Any]:
    config = build_security_configuration(app)
    secret_report = scan_repository()
    dependency_report = validate_dependencies()
    policy = build_security_policy(app)
    warnings: list[str] = list(secret_report.get("warnings", [])) + list(dependency_report.get("warnings", []))
    errors: list[str] = list(secret_report.get("errors", [])) + list(dependency_report.get("errors", []))
    if not config.get("security_enabled", True):
        warnings.append("Security hardening is disabled.")
    if not config.get("security_headers_enabled", True):
        warnings.append("Security headers are disabled.")
    if not config.get("rate_limiting_enabled", True):
        warnings.append("Rate limiting is disabled.")
    if not config.get("input_sanitization_enabled", True):
        warnings.append("Input sanitization is disabled.")
    if not config.get("output_sanitization_enabled", True):
        warnings.append("Output sanitization is disabled.")
    warnings.extend(list(policy.get("warnings", [])))
    jwt_secret = str(os.getenv("JWT_SECRET_KEY", "")).strip()
    jwt_warnings: list[str] = []
    jwt_errors: list[str] = []
    if not jwt_secret:
        jwt_warnings.append("JWT secret is missing.")
    elif len(jwt_secret) < 16:
        jwt_errors.append("JWT secret is too short.")
    demo_secret = "x" * 32
    demo_token = create_access_token({"sub": "system", "iss": "security"}, expires_in_hours=1, secret=demo_secret)
    return {
        "valid": not errors,
        "warnings": warnings,
        "errors": errors,
        "secret_scan": secret_report,
        "dependencies": dependency_report,
        "policy": policy,
        "configuration": config,
        "checks": {
            "input_sanitizer": validate_input("safe"),
            "output_sanitizer": validate_output({"safe": True}),
            "path_security": validate_path("data/safe.json"),
            "jwt_security": {"valid": bool(demo_token), "warnings": jwt_warnings, "errors": jwt_errors},
            "auth_security": build_auth_security_summary({"status": "active", "role": "viewer", "user_id": "system"}),
            "rbac_security": build_rbac_security_summary(
                actor={"user_id": "system", "role": "admin", "permissions": ["admin:all", "user:manage"]},
                target={"user_id": "target", "role": "viewer"},
            ),
        },
    }
