"""Write storage records and snapshots."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from src.reporting.report_metrics import safe_text
from src.storage.json_store import write_json
from src.storage.markdown_store import render_record_markdown, write_markdown
from src.storage.storage_index import StorageIndex
from src.storage.storage_paths import build_record_path, ensure_storage_dirs


class StorageWriter:
    """Persist storage records to disk."""

    def __init__(self, storage_root: str | Path = "data", index: StorageIndex | None = None) -> None:
        self.storage_root = Path(storage_root)
        self.index = index or StorageIndex(storage_root=self.storage_root)
        ensure_storage_dirs(self.storage_root)

    def write_record(self, record: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        """Write a storage record as JSON and optionally markdown."""

        try:
            record_type = safe_text(record.get("record_type"), limit=80)
            record_id = safe_text(record.get("record_id"), limit=160)
            path = build_record_path(record_type, record_id, extension="json", storage_root=self.storage_root)
            json_result = write_json(path, record, overwrite=overwrite)
            markdown_path = ""
            markdown_result = {"success": True, "path": "", "warnings": [], "errors": []}
            if json_result.get("success") and write_markdown:
                markdown_path = str(path.with_suffix(".md"))
                markdown_result = write_markdown_fn(Path(markdown_path), render_record_markdown(record), overwrite=overwrite)
            index_result = self.index.update(record, str(path)) if json_result.get("success") else {"success": False, "warnings": [], "errors": []}
            return {
                "success": bool(json_result.get("success")) and bool(index_result.get("success", True)) and bool(markdown_result.get("success", True)),
                "record_type": record_type,
                "record_id": record_id,
                "path": str(path),
                "markdown_path": markdown_path,
                "warnings": list(dict.fromkeys(json_result.get("warnings", []) + markdown_result.get("warnings", []) + index_result.get("warnings", []))),
                "errors": list(dict.fromkeys(json_result.get("errors", []) + markdown_result.get("errors", []) + index_result.get("errors", []))),
                "index_result": index_result,
            }
        except Exception as exc:
            return {"success": False, "record_type": safe_text(record.get("record_type"), limit=80), "record_id": safe_text(record.get("record_id"), limit=160), "path": "", "markdown_path": "", "warnings": [], "errors": [str(exc)]}

    def write_snapshot(self, snapshot: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
        """Write a snapshot JSON file."""

        record_id = safe_text(snapshot.get("snapshot_id"), limit=160) or safe_text(snapshot.get("record_id"), limit=160)
        path = build_record_path("snapshot", record_id, extension="json", storage_root=self.storage_root)
        return write_json(path, snapshot, overwrite=overwrite)


def write_markdown_fn(path: Path, content: str, overwrite: bool = False) -> dict[str, Any]:
    """Internal wrapper to avoid name shadowing."""

    return write_markdown(path, content, overwrite=overwrite)
