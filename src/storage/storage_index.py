"""Maintain local storage indexes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from src.reports.markdown_utils import safe_text
from src.storage.storage_paths import STORAGE_ROOT, ensure_storage_dirs, sanitize_filename


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""

    return datetime.now(timezone.utc).isoformat()


class StorageIndex:
    """Maintain flat and segmented storage index files."""

    def __init__(self, storage_root: str | Path = STORAGE_ROOT) -> None:
        self.storage_root = Path(storage_root)
        self.index_root = self.storage_root / "indexes"
        ensure_storage_dirs(self.storage_root)
        self.index_root.mkdir(parents=True, exist_ok=True)

    def update(self, record: dict[str, Any], path: str) -> dict[str, Any]:
        """Update index files for a stored record."""

        entry = self._build_entry(record, path)
        updates = {
            "type": self.index_root / f"type_{sanitize_filename(entry['record_type'])}.json",
            "brand": self.index_root / f"brand_{sanitize_filename(entry['brand'] or 'unknown')}.json",
            "campaign": self.index_root / f"campaign_{sanitize_filename(entry['campaign_type'] or 'unknown')}.json",
            "execution": self.index_root / f"execution_{sanitize_filename(entry['execution_id'] or 'unknown')}.json",
            "latest": self.index_root / "latest.json",
        }
        results: dict[str, Any] = {"success": True, "warnings": [], "errors": [], "updated_files": {}}
        for _, index_path in updates.items():
            result = self._append_entry(index_path, entry)
            results["updated_files"][str(index_path)] = result
            if not result.get("success"):
                results["success"] = False
                results["errors"].extend(result.get("errors", []))
        return results

    def read_index(self, name: str) -> dict[str, Any]:
        """Read an index file by name."""

        path = self.index_root / f"{sanitize_filename(name)}.json"
        if not path.exists():
            return {"success": False, "path": str(path), "records": [], "warnings": [], "errors": ["Index not found."]}
        try:
            return {"success": True, "path": str(path), **json.loads(path.read_text(encoding="utf-8"))}
        except Exception as exc:
            return {"success": False, "path": str(path), "records": [], "warnings": [], "errors": [str(exc)]}

    def _build_entry(self, record: dict[str, Any], path: str) -> dict[str, Any]:
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        return {
            "record_id": safe_text(record.get("record_id"), limit=160),
            "record_type": safe_text(record.get("record_type"), limit=80),
            "path": safe_text(path, limit=260),
            "brand": safe_text(record.get("brand") or metadata.get("brand"), limit=80),
            "platform": safe_text(record.get("platform") or metadata.get("platform"), limit=80),
            "content_type": safe_text(record.get("content_type") or metadata.get("content_type"), limit=80),
            "campaign_type": safe_text(record.get("campaign_type") or metadata.get("campaign_type"), limit=80),
            "execution_id": safe_text(record.get("execution_id") or metadata.get("execution_id"), limit=120),
            "created_at": safe_text(record.get("created_at"), limit=80),
        }

    def _append_entry(self, index_path: Path, entry: dict[str, Any]) -> dict[str, Any]:
        try:
            index_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"updated_at": utc_now_iso(), "records": []}
            if index_path.exists():
                try:
                    payload = json.loads(index_path.read_text(encoding="utf-8"))
                except Exception:
                    payload = {"updated_at": utc_now_iso(), "records": []}
            records = [item for item in payload.get("records", []) if item.get("record_id") != entry["record_id"]]
            records.insert(0, entry)
            payload = {"updated_at": utc_now_iso(), "records": records[:1000]}
            index_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            return {"success": True, "path": str(index_path), "warnings": [], "errors": []}
        except Exception as exc:
            return {"success": False, "path": str(index_path), "warnings": [], "errors": [str(exc)]}
