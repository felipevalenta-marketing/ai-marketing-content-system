"""Local helpers for markdown report generation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import json

from src.utils.file_utils import normalize_key


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_text(value: Any, limit: int = 240) -> str:
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
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_bool(value: Any) -> bool:
    return bool(value)


def safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if value in (None, "", {}, []):
        return []
    return [value]


def unique_strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        values = safe_list(values)
    cleaned = [safe_text(item, limit=120) for item in values]
    return list(dict.fromkeys([item for item in cleaned if item]))


def safe_filename(value: str, fallback: str = "report") -> str:
    cleaned = normalize_key(value).replace("/", "_").replace("\\", "_")
    cleaned = cleaned.replace(":", "_").replace(" ", "_")
    return cleaned or fallback


def compact_value(value: Any, limit: int = 240, max_items: int = 4) -> str:
    """Render nested values as a concise human-readable string."""

    if value is None:
        return ""
    if isinstance(value, str):
        return safe_text(value, limit=limit)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return safe_text(value, limit=limit)
    if isinstance(value, dict):
        parts: list[str] = []
        for index, (key, item) in enumerate(value.items()):
            if index >= max_items:
                parts.append("...")
                break
            item_text = compact_value(item, limit=max(32, limit // 2), max_items=max_items)
            if item_text:
                parts.append(f"{safe_text(key, limit=48)}: {item_text}")
        return safe_text("; ".join(parts), limit=limit)
    if isinstance(value, list):
        parts = []
        for index, item in enumerate(value):
            if index >= max_items:
                parts.append("...")
                break
            item_text = compact_value(item, limit=max(32, limit // 2), max_items=max_items)
            if item_text:
                parts.append(item_text)
        return safe_text(", ".join(parts), limit=limit)
    return safe_text(value, limit=limit)
