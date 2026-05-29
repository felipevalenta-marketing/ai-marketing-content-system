"""Sanitize observability payloads before logging."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from src.reports.markdown_utils import safe_text


SENSITIVE_KEY_TOKENS = {
    "api_key",
    "password",
    "secret",
    "bearer",
    "token",
    "authorization",
    "refresh_token",
    "access_token",
    "id_token",
    "jwt_secret",
    "openai_api_key",
    "provider_credentials",
    "raw_response",
    "raw_prompt",
    "prompt",
    "context",
    "dotenv",
}

SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"OPENAI_API_KEY", re.IGNORECASE),
    re.compile(r"JWT_SECRET_KEY", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"\bbearer\s+[A-Za-z0-9\-\._~\+/=]{8,}\b", re.IGNORECASE),
    re.compile(r"\b[A-Za-z0-9_\-]*secret[A-Za-z0-9_\-]*\b", re.IGNORECASE),
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\bapi_key\b", re.IGNORECASE),
)

SAFE_VALUE_KEYS = {
    "token_usage",
    "cost_usage",
    "total_tokens",
    "input_tokens",
    "output_tokens",
    "cached_input_tokens",
    "total_cost",
    "input_cost",
    "output_cost",
    "cached_input_cost",
    "provider",
    "model",
    "record_id",
    "workflow_id",
    "request_id",
    "organization_id",
    "team_id",
    "duration_ms",
}


def redact_log_value(value: Any, key: str = "") -> Any:
    key_text = safe_text(key, limit=120).lower()
    if key_text and _is_sensitive_key(key_text):
        if key_text.endswith("_present"):
            return bool(value)
        return "[redacted]"
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for item_key, item_value in value.items():
            cleaned_key = safe_text(item_key, limit=120)
            if _is_sensitive_key(cleaned_key.lower()):
                redacted[cleaned_key] = "[redacted]"
            else:
                redacted[cleaned_key] = redact_log_value(item_value, cleaned_key)
        return redacted
    if isinstance(value, list):
        return [redact_log_value(item, key_text) for item in value]
    if isinstance(value, str):
        if _looks_like_path(value):
            return Path(value).name or "[path]"
        if any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS):
            return "[redacted]"
        if key_text not in SAFE_VALUE_KEYS:
            return safe_text(value, limit=260)
        return safe_text(value, limit=520)
    return value


def redact_log_payload(payload: Any) -> Any:
    return redact_log_value(payload)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in {"openai_api_key_present", "jwt_secret_key_present", "auth_config_present"}:
        return False
    if normalized in SAFE_VALUE_KEYS:
        return False
    return any(token in normalized for token in SENSITIVE_KEY_TOKENS)


def _looks_like_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized) is not None
