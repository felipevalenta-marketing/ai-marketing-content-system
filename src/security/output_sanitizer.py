"""Output sanitization helpers."""

from __future__ import annotations

from typing import Any

from src.observability.log_sanitizer import redact_log_payload
from src.reports.markdown_utils import safe_text


def sanitize_output(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text.endswith("_present") or key_text in {"openai_api_key_present", "jwt_secret_key_present", "auth_config_present"}:
                sanitized[str(key)] = bool(item)
                continue
            if key_text in {"markdown", "content", "text", "html"} and isinstance(item, str):
                redacted = redact_log_payload(item)
                if redacted == "[redacted]":
                    sanitized[str(key)] = redacted
                else:
                    sanitized[str(key)] = safe_text(item, limit=50000)
                continue
            allowed_token_keys = {
                "access_token",
                "token_type",
                "token_usage",
                "token_summary",
                "workflow_token_summary",
                "estimated_token_usage",
                "execution_token_summary",
                "module_token_summary",
                "provider_token_summary",
                "token_provider",
                "token_model",
                "token_source",
                "total_tokens",
                "input_tokens",
                "output_tokens",
                "cached_input_tokens",
                "cost_total",
                "total_cost",
            }
            if any(token in key_text for token in {"password_hash", "jwt_secret", "openai_api_key", "api_key", "bearer", "secret", "token"}) and key_text not in allowed_token_keys:
                sanitized[str(key)] = "[redacted]"
            else:
                sanitized[str(key)] = sanitize_output(item)
        return sanitized
    if isinstance(value, list):
        return [sanitize_output(item) for item in value]
    return redact_log_payload(value)


def validate_output(value: Any) -> dict[str, Any]:
    sanitized = sanitize_output(value)
    return {"valid": True, "warnings": [], "errors": [], "value": sanitized}
