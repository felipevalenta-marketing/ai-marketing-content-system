"""Shared helpers for normalized reporting metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json

from src.utils.file_utils import normalize_key


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""

    return datetime.now(timezone.utc).isoformat()


def safe_text(value: Any, limit: int = 240) -> str:
    """Convert a value to a compact text representation."""

    if value is None:
        return ""
    if isinstance(value, str):
        text = value.strip()
    elif isinstance(value, (dict, list, tuple, set)):
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            text = str(value)
    else:
        text = str(value).strip()
    if len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def safe_float(value: Any, default: float = 0.0) -> float:
    """Coerce a value into a float safely."""

    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Coerce a value into an int safely."""

    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value: Any) -> bool:
    """Return a safe boolean interpretation of a value."""

    return bool(value)


def safe_dict(value: Any) -> dict[str, Any]:
    """Return a dictionary or an empty fallback."""

    return dict(value) if isinstance(value, dict) else {}


def safe_list(value: Any) -> list[Any]:
    """Return a list or an empty fallback."""

    if isinstance(value, list):
        return list(value)
    if value in (None, "", {}, []):
        return []
    return [value]


def unique_strings(values: Any) -> list[str]:
    """Normalize a sequence into unique, non-empty strings."""

    if not isinstance(values, list):
        values = safe_list(values)
    cleaned = [safe_text(item, limit=120) for item in values]
    return list(dict.fromkeys([item for item in cleaned if item]))


def percentage(part: float, total: float) -> float:
    """Return a safe percentage."""

    if total <= 0:
        return 0.0
    return round((part / total) * 100.0, 2)


def count_truthy(values: Any) -> int:
    """Count truthy values in a collection."""

    if not isinstance(values, list):
        values = safe_list(values)
    return sum(1 for value in values if bool(value))


def normalize_counts(items: Any) -> dict[str, int]:
    """Count normalized string values from a sequence."""

    counts: dict[str, int] = {}
    if not isinstance(items, list):
        items = safe_list(items)
    for item in items:
        key = normalize_key(safe_text(item, limit=120))
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def safe_filename(value: str, fallback: str = "report") -> str:
    """Create a filesystem-safe filename segment."""

    cleaned = normalize_key(value).replace("/", "_").replace("\\", "_")
    cleaned = cleaned.replace(":", "_").replace(" ", "_")
    return cleaned or fallback


def summarize_status_counts(items: Any, field_name: str = "status") -> dict[str, int]:
    """Count item statuses from a list of dictionaries."""

    counts: dict[str, int] = {}
    if not isinstance(items, list):
        items = safe_list(items)
    for item in items:
        status = "unknown"
        if isinstance(item, dict):
            status = safe_text(item.get(field_name, "unknown"), limit=80).lower() or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts
