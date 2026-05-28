"""Validate storage records before persistence."""

from __future__ import annotations

from typing import Any
import json
import re

from src.reporting.report_metrics import safe_dict, safe_list, safe_text
from src.storage.storage_contracts import SUPPORTED_STORAGE_RECORD_TYPES


SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"bearer\s+[A-Za-z0-9\-\._~\+/=]{8,}", re.IGNORECASE),
)

SAFE_TOKEN_KEYS = {
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cached_input_tokens",
    "estimated_tokens",
    "token_usage",
    "token_summary",
    "estimated_token_usage",
    "execution_token_summary",
    "module_token_summary",
    "provider_token_summary",
    "token_provider",
    "token_model",
    "token_source",
    "token_metrics_present",
}


class StorageValidator:
    """Validate storage records and file paths."""

    def validate(self, record: dict[str, Any]) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}

        if not isinstance(record, dict):
            return {"valid": False, "warnings": [], "errors": ["Record must be a dictionary."], "checks": {}}

        record_id = safe_text(record.get("record_id"), limit=160)
        record_type = safe_text(record.get("record_type"), limit=80)
        created_at = safe_text(record.get("created_at"), limit=80)
        payload = record.get("payload")
        metadata_raw = record.get("metadata")
        warnings_raw = record.get("warnings")
        errors_raw = record.get("errors")
        metadata = safe_dict(metadata_raw)
        warnings_list = safe_list(warnings_raw)
        errors_list = safe_list(errors_raw)

        checks["record_id_present"] = bool(record_id)
        checks["record_type_supported"] = record_type in SUPPORTED_STORAGE_RECORD_TYPES
        checks["created_at_present"] = bool(created_at)
        checks["payload_present"] = payload is not None
        checks["metadata_is_dict"] = isinstance(metadata_raw, dict)
        checks["warnings_is_list"] = isinstance(warnings_raw, list)
        checks["errors_is_list"] = isinstance(errors_raw, list)
        checks["json_serializable"] = self._is_json_serializable(record)
        checks["no_secrets"] = not self._contains_secret(record)

        if not record_id:
            errors.append("record_id is required.")
        if not checks["record_type_supported"]:
            errors.append(f"Unsupported record_type: {record_type}")
        if not created_at:
            errors.append("created_at is required.")
        if payload is None:
            errors.append("payload is required.")
        if not checks["metadata_is_dict"]:
            errors.append("metadata must be a dictionary.")
        if not checks["warnings_is_list"]:
            errors.append("warnings must be a list.")
        if not checks["errors_is_list"]:
            errors.append("errors must be a list.")
        if not checks["json_serializable"]:
            errors.append("Record must be JSON serializable.")
        if not checks["no_secrets"]:
            errors.append("Record contains sensitive information.")

        return {"valid": not errors, "warnings": warnings, "errors": errors, "checks": checks}

    def validate_path(self, path: str) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}
        candidate = safe_text(path, limit=512)
        checks["safe_path"] = not self._looks_unsafe(candidate)
        if not checks["safe_path"]:
            errors.append("Unsafe storage path detected.")
        return {"valid": not errors, "warnings": warnings, "errors": errors, "checks": checks}

    def _contains_secret(self, value: Any) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = safe_text(key, limit=80).lower()
                if any(marker in key_text for marker in ("api_key", "password", "secret", "token")):
                    if key_text not in SAFE_TOKEN_KEYS:
                        return True
                if self._contains_secret(item):
                    return True
            return False
        if isinstance(value, list):
            return any(self._contains_secret(item) for item in value)
        if isinstance(value, str):
            lower = value.lower()
            if "openai_api_key" in lower:
                return True
            if any(pattern.search(value) for pattern in SECRET_PATTERNS):
                return True
            if re.search(r"(?i)\b(api_key|password|secret)\b", value):
                return True
        return False

    def _is_json_serializable(self, value: Any) -> bool:
        try:
            json.dumps(value, default=str)
            return True
        except Exception:
            return False

    def _looks_unsafe(self, path: str) -> bool:
        normalized = path.replace("\\", "/")
        return ".." in normalized or normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized) is not None
