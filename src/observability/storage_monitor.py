"""Storage observability helpers."""

from __future__ import annotations

from typing import Any
from pathlib import Path

from src.reporting.report_metrics import safe_text


def build_storage_observability(storage_manager: Any | None = None, *, limit: int = 20) -> dict[str, Any]:
    if storage_manager is None:
        return {
            "storage_root_exists": False,
            "storage_root_writable": False,
            "record_count": 0,
            "latest_record_timestamp": "",
            "warnings": ["Storage manager unavailable."],
            "errors": [],
        }
    storage_root = Path(getattr(storage_manager, "storage_root", "data"))
    index = getattr(storage_manager, "index", None)
    latest_records = []
    latest_timestamp = ""
    record_count = 0
    warnings: list[str] = []
    errors: list[str] = []
    try:
        if index is not None and hasattr(index, "read_index"):
            latest = index.read_index("latest")
            latest_records = list(latest.get("records", []))[: max(0, int(limit or 20))]
            record_count = len(latest.get("records", []))
            if latest_records:
                latest_timestamp = safe_text(latest_records[0].get("created_at"), limit=80)
    except Exception as exc:
        warnings.append("Storage index unavailable.")
        errors.append(str(exc))
    return {
        "storage_root_exists": storage_root.exists(),
        "storage_root_writable": _is_writable(storage_root),
        "record_count": record_count,
        "latest_record_timestamp": latest_timestamp,
        "recent_records": latest_records,
        "warnings": warnings,
        "errors": errors,
    }


def _is_writable(storage_root: Path) -> bool:
    if not storage_root.exists():
        return False
    try:
        probe = storage_root / ".observability-write-check"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False
