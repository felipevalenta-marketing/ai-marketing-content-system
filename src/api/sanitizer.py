"""Sanitize API responses before returning them to clients."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re

from src.reports.markdown_utils import safe_text


SENSITIVE_KEY_TOKENS = {
    "api_key",
    "password",
    "secret",
    "bearer",
    "raw_response",
    "provider_response",
    "openai_raw_response",
    "prompt_payload",
    "prompt_text",
    "context",
    "context_summary",
    "knowledge_base",
    "brand_context",
    "raw_context",
    "provider_credentials",
    "access_token",
    "refresh_token",
}

SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"OPENAI_API_KEY", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"\bbearer\s+[A-Za-z0-9\-\._~\+/=]{8,}\b", re.IGNORECASE),
    re.compile(r"\bapi_key\b", re.IGNORECASE),
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
)


def sanitize_api_payload(value: Any) -> Any:
    return _sanitize(value, parent_key="")


def _sanitize(value: Any, parent_key: str) -> Any:
    key = safe_text(parent_key, limit=120).lower()
    if key and _is_sensitive_key(key):
        return "[redacted]"
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for item_key, item_value in value.items():
            cleaned_key = safe_text(item_key, limit=120)
            if _is_sensitive_key(cleaned_key.lower()):
                result[cleaned_key] = "[redacted]"
                continue
            sanitized = _sanitize(item_value, cleaned_key)
            if sanitized is not None:
                result[cleaned_key] = sanitized
        return result
    if isinstance(value, list):
        return [_sanitize(item, parent_key) for item in value]
    if isinstance(value, str):
        if _looks_like_absolute_path(value):
            path = Path(value)
            return path.name or "[path]"
        if any(pattern.search(value) for pattern in SENSITIVE_VALUE_PATTERNS):
            return "[redacted]"
        limit = 40000 if _is_long_text_key(key) else 2200
        return safe_text(value, limit=limit)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    try:
        json.dumps(value, default=str)
        return safe_text(value, limit=1200)
    except Exception:
        return safe_text(str(value), limit=1200)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    if normalized in {"openai_api_key_present", "api_key_present"} or normalized.endswith("_present") and "api_key" in normalized:
        return False
    if normalized in {"token", "access_token", "token_usage", "token_summary", "input_tokens", "output_tokens", "total_tokens", "cached_input_tokens", "estimated_tokens", "token_source", "token_provider", "token_model"}:
        return False
    return any(token in normalized for token in SENSITIVE_KEY_TOKENS)


def _is_long_text_key(key: str) -> bool:
    return key in {
        "markdown",
        "markdown_report",
        "rendered_markdown",
        "rendered_text",
        "content",
        "caption",
        "script",
        "voiceover",
        "summary",
        "title",
        "report",
        "markdown_preview",
    }


def _looks_like_absolute_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized) is not None
