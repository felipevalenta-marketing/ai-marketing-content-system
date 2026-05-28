"""Optional markdown persistence helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.reporting.report_metrics import safe_text


def render_record_markdown(record: dict[str, Any]) -> str:
    """Render a storage record into a readable markdown summary."""

    lines = [
        f"# {safe_text(record.get('record_type', 'record'), limit=80).replace('_', ' ').title()}",
        "",
        f"- **Record ID**: {safe_text(record.get('record_id', ''), limit=120)}",
        f"- **Brand**: {safe_text(record.get('brand', ''), limit=120)}",
        f"- **Platform**: {safe_text(record.get('platform', ''), limit=120)}",
        f"- **Content Type**: {safe_text(record.get('content_type', ''), limit=120)}",
        f"- **Campaign Type**: {safe_text(record.get('campaign_type', ''), limit=120)}",
        f"- **Execution ID**: {safe_text(record.get('execution_id', ''), limit=120)}",
        "",
        "## Payload",
        "",
        "```json",
        safe_text(record.get("payload", {}), limit=5000),
        "```",
    ]
    return "\n".join(lines).strip()


def write_markdown(path: Path, content: str, overwrite: bool = False) -> dict[str, Any]:
    """Write markdown content safely."""

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            return {"success": False, "path": str(path), "error": "File already exists.", "warnings": [], "errors": ["File already exists."]}
        path.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(path), "warnings": [], "errors": []}
    except Exception as exc:
        return {"success": False, "path": str(path), "error": str(exc), "warnings": [], "errors": [str(exc)]}
