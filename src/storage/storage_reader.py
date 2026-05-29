"""Read and search storage records."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from src.reports.markdown_utils import safe_dict, safe_text
from src.storage.storage_contracts import SUPPORTED_STORAGE_RECORD_TYPES
from src.storage.storage_index import StorageIndex
from src.storage.storage_paths import STORAGE_ROOT, build_record_path, ensure_storage_dirs, get_record_folder


class StorageReader:
    """Read stored records from disk."""

    def __init__(self, storage_root: str | Path = STORAGE_ROOT, index: StorageIndex | None = None) -> None:
        self.storage_root = Path(storage_root)
        self.index = index or StorageIndex(storage_root=self.storage_root)
        ensure_storage_dirs(self.storage_root)

    def read_record(self, record_type: str, record_id: str) -> dict[str, Any]:
        """Read a single record by type and id."""

        if safe_text(record_type, limit=80) not in SUPPORTED_STORAGE_RECORD_TYPES:
            return {"success": False, "record": {}, "path": "", "warnings": [], "errors": [f"Unsupported storage record_type: {record_type}"]}
        path = self._path_for(record_type, record_id)
        try:
            if not path.exists():
                return {"success": False, "record": {}, "path": str(path), "warnings": [], "errors": ["Record not found."]}
            return {"success": True, "record": json.loads(path.read_text(encoding="utf-8")), "path": str(path), "warnings": [], "errors": []}
        except Exception as exc:
            return {"success": False, "record": {}, "path": str(path), "warnings": [], "errors": [str(exc)]}

    def list_records(self, record_type: str | None = None) -> list[dict[str, Any]]:
        """List records by type or all records."""

        paths: list[Path] = []
        if record_type:
            paths = list(self._folder_for(record_type).rglob("*.json"))
        else:
            paths = list((self.storage_root).rglob("*.json"))
        records: list[dict[str, Any]] = []
        for path in sorted(paths):
            if "indexes" in path.parts:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                records.append(data)
            except Exception:
                continue
        return records

    def find_records(self, filters: dict[str, Any]) -> list[dict[str, Any]]:
        """Find records by exact metadata filters."""

        filtered: list[dict[str, Any]] = []
        for record in self.list_records():
            if self._matches(record, filters):
                filtered.append(record)
        return filtered

    def latest_records(self, record_type: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return the latest records for a type."""

        index = self.index.read_index(f"type_{safe_text(record_type, limit=80)}")
        records = safe_dict(index).get("records", []) if isinstance(index, dict) else []
        if records:
            return [entry for entry in records[: max(0, limit)]]
        return self.list_records(record_type=record_type)[: max(0, limit)]

    def _path_for(self, record_type: str, record_id: str) -> Path:
        return build_record_path(record_type, safe_text(record_id, limit=160), storage_root=self.storage_root)

    def _folder_for(self, record_type: str) -> Path:
        return get_record_folder(record_type, storage_root=self.storage_root)

    def _matches(self, record: dict[str, Any], filters: dict[str, Any]) -> bool:
        if not isinstance(record, dict):
            return False
        metadata = safe_dict(record.get("metadata"))
        for key, expected in (filters or {}).items():
            actual = record.get(key, metadata.get(key))
            if str(actual).strip() != str(expected).strip():
                return False
        return True
