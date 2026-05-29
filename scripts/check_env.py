from __future__ import annotations

import json
import os
from pathlib import Path


def _env_flag(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return default


def _looks_like_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {
        "replace_with_secure_random_value",
        "change_me",
        "change-this",
        "your_jwt_secret_key",
        "your_openai_api_key_here",
        "placeholder",
    }


def _secret_present(value: str) -> bool:
    return bool(value.strip()) and not _looks_like_placeholder(value)


def validate_environment() -> dict[str, object]:
    app_env_raw = os.getenv("APP_ENV")
    app_env = (app_env_raw or "development").strip() or "development"
    warnings: list[str] = []
    errors: list[str] = []

    jwt_secret = os.getenv("JWT_SECRET_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    storage_root = Path(os.getenv("STORAGE_ROOT", "data"))
    api_port = os.getenv("API_PORT", "8000").strip()
    app_env_present = app_env_raw is not None
    jwt_secret_present = _secret_present(jwt_secret)
    openai_key_present = _secret_present(openai_key)
    storage_root_ready = False

    try:
        port_value = int(api_port)
        if port_value <= 0 or port_value > 65535:
            raise ValueError
    except ValueError:
        errors.append("API_PORT must be a valid TCP port number.")

    if not app_env_present:
        warnings.append("APP_ENV is not set; defaulting to development.")

    if app_env == "production":
        if not jwt_secret_present:
            errors.append("JWT_SECRET_KEY is required in production.")
        elif len(jwt_secret) < 16:
            warnings.append("JWT_SECRET_KEY is short; use a stronger secret.")
        if not openai_key_present:
            errors.append("OPENAI_API_KEY is required in production.")
    else:
        if not jwt_secret_present:
            warnings.append("JWT_SECRET_KEY is not set; authentication will use a test-only fallback when allowed.")
        if not openai_key_present:
            warnings.append("OPENAI_API_KEY is not set; generation will rely on dry-run or mocked flows.")

    if not storage_root.exists():
        try:
            storage_root.mkdir(parents=True, exist_ok=True)
        except Exception:
            errors.append("Storage root could not be created.")
        else:
            storage_root_ready = True
    else:
        storage_root_ready = True

    if storage_root_ready:
        try:
            test_file = storage_root / ".write-test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
        except Exception:
            errors.append("Storage root is not writable.")

    if not _env_flag("ENABLE_AUTHENTICATION", True):
        warnings.append("Authentication is disabled.")

    return {
        "success": not errors,
        "environment": app_env,
        "app_env_present": app_env_present,
        "APP_ENV_PRESENT": app_env_present,
        "openai_api_key_present": openai_key_present,
        "OPENAI_API_KEY_PRESENT": openai_key_present,
        "jwt_secret_key_present": jwt_secret_present,
        "JWT_SECRET_KEY_PRESENT": jwt_secret_present,
        "auth_config_present": jwt_secret_present,
        "storage_root": str(storage_root),
        "storage_root_ready": storage_root_ready and not any("Storage root" in error for error in errors),
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    result = validate_environment()
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
