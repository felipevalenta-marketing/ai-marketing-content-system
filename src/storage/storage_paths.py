"""Safe filesystem path helpers for persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import re

from src.reporting.report_metrics import safe_text


STORAGE_ROOT = Path("data")

RECORD_FOLDER_MAP = {
    "execution": "executions",
    "generation": "generations",
    "campaign": "campaigns",
    "asset": "assets",
    "report": "reports",
    "token_usage": "tracking/tokens",
    "cost_usage": "tracking/costs",
    "creative_direction": "snapshots",
    "image_prompt": "snapshots",
    "video_script": "snapshots",
    "snapshot": "snapshots",
}


def sanitize_filename(value: str) -> str:
    """Return a filename-safe string without traversal characters."""

    text = safe_text(value, limit=240).strip().lower()
    text = text.replace("\\", "_").replace("/", "_").replace("..", "_")
    text = re.sub(r"[^a-z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("._-") or "record"


def build_record_id(record_type: str, metadata: dict[str, Any] | None = None) -> str:
    """Build a safe record id from metadata and timestamp."""

    meta = metadata or {}
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    brand = sanitize_filename(str(meta.get("brand", ""))) if meta.get("brand") else ""
    execution_id = sanitize_filename(str(meta.get("execution_id", ""))) if meta.get("execution_id") else ""
    campaign_id = sanitize_filename(str(meta.get("campaign_id", ""))) if meta.get("campaign_id") else ""
    seed_parts = [sanitize_filename(record_type)]
    for part in (brand, execution_id, campaign_id):
        if part:
            seed_parts.append(part)
    seed_parts.append(timestamp)
    return "_".join(seed_parts)


def get_record_folder(record_type: str, storage_root: str | Path | None = None) -> Path:
    """Return the folder for a record type."""

    folder = RECORD_FOLDER_MAP.get(sanitize_filename(record_type), "snapshots")
    root = Path(storage_root) if storage_root is not None else STORAGE_ROOT
    return root / folder


def build_record_path(record_type: str, record_id: str, extension: str = "json", storage_root: str | Path | None = None) -> Path:
    """Build a safe path for a storage record."""

    root = Path(storage_root) if storage_root is not None else STORAGE_ROOT
    raw_record_id = safe_text(record_id, limit=240)
    if _looks_unsafe_path_component(raw_record_id):
        raise ValueError("Unsafe storage path detected.")
    folder = get_record_folder(record_type, storage_root=root)
    filename = f"{sanitize_filename(raw_record_id)}.{sanitize_filename(extension).lstrip('.') or 'json'}"
    path = (folder / filename).resolve()
    root_resolved = root.resolve()
    if root_resolved not in path.parents and path != root_resolved:
        raise ValueError("Unsafe storage path detected.")
    return path


def ensure_storage_dirs(storage_root: str | Path | None = None) -> None:
    """Create the default storage directory structure."""

    root = Path(storage_root) if storage_root is not None else STORAGE_ROOT
    for folder in set(RECORD_FOLDER_MAP.values()) | {"indexes"}:
        (root / folder).mkdir(parents=True, exist_ok=True)


def _looks_unsafe_path_component(value: str) -> bool:
    normalized = value.replace("\\", "/")
    return ".." in normalized or normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized) is not None
