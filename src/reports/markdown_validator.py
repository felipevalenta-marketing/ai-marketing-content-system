"""Validate markdown reports for safety and structure."""

from __future__ import annotations

from typing import Any
import json
import re

from src.reports.markdown_contracts import SUPPORTED_MARKDOWN_REPORT_TYPES
from src.reports.markdown_utils import safe_text


SECRET_PATTERNS = (
    re.compile(r"OPENAI_API_KEY", re.IGNORECASE),
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"\bbearer\s+[A-Za-z0-9\-\._~\+/=]{8,}\b", re.IGNORECASE),
    re.compile(r"\bapi_key\b", re.IGNORECASE),
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\bsecret\b", re.IGNORECASE),
    re.compile(r"\.env", re.IGNORECASE),
)


class MarkdownValidator:
    """Validate markdown report content and export metadata."""

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        warnings: list[str] = []
        errors: list[str] = []

        report_type = safe_text(payload.get("report_type"), limit=80)
        title = safe_text(payload.get("title"), limit=160)
        markdown = safe_text(payload.get("markdown"), limit=500000)
        export_path = safe_text(payload.get("export_path"), limit=512)
        metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}

        if not report_type:
            errors.append("report_type is required.")
        elif report_type not in SUPPORTED_MARKDOWN_REPORT_TYPES:
            errors.append(f"Unsupported markdown report_type: {report_type}")

        if not title:
            warnings.append("Report title is missing; a fallback title may be used.")

        if not markdown.strip():
            errors.append("markdown is required.")
        if self._contains_secret(markdown) or self._contains_secret(metadata):
            errors.append("Markdown report contains sensitive information.")
        if "raw_response" in markdown.lower() or "provider_response" in markdown.lower():
            errors.append("Markdown report appears to include raw provider output.")
        if markdown.strip() and "## " not in markdown:
            warnings.append("Markdown report has no major sections.")
        if markdown.strip() and len(markdown.splitlines()) > 800:
            warnings.append("Markdown report is long; consider tightening section content.")
        if export_path and not self._is_safe_path(export_path):
            errors.append("Unsafe markdown export path detected.")
        if not self._is_json_serializable(payload):
            errors.append("Markdown payload must be JSON serializable.")

        return {"valid": not errors, "warnings": warnings, "errors": errors}

    def _contains_secret(self, value: Any) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                key_text = safe_text(key, limit=80).lower()
                if any(marker in key_text for marker in ("api_key", "password", "secret")):
                    return True
                if self._contains_secret(item):
                    return True
            return False
        if isinstance(value, list):
            return any(self._contains_secret(item) for item in value)
        if isinstance(value, str):
            return any(pattern.search(value) for pattern in SECRET_PATTERNS)
        return False

    def _is_safe_path(self, value: str) -> bool:
        normalized = value.replace("\\", "/")
        if ".." in normalized:
            return False
        if normalized.startswith("//"):
            return False
        return True

    def _is_json_serializable(self, value: Any) -> bool:
        try:
            json.dumps(value, default=str)
            return True
        except Exception:
            return False
