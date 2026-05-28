"""Safe JSON persistence helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import tempfile


def write_json(path: Path, data: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
    """Write a JSON file atomically when possible."""

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            return {"success": False, "path": str(path), "error": "File already exists.", "warnings": [], "errors": ["File already exists."]}
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=str(path.parent), suffix=".tmp") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False, default=str)
            temp_name = handle.name
        Path(temp_name).replace(path)
        return {"success": True, "path": str(path), "warnings": [], "errors": []}
    except Exception as exc:
        return {"success": False, "path": str(path), "error": str(exc), "warnings": [], "errors": [str(exc)]}


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON file safely."""

    try:
        if not path.exists():
            return {"success": False, "path": str(path), "record": {}, "warnings": [], "errors": ["File not found."]}
        with path.open("r", encoding="utf-8") as handle:
            return {"success": True, "path": str(path), "record": json.load(handle), "warnings": [], "errors": []}
    except Exception as exc:
        return {"success": False, "path": str(path), "record": {}, "warnings": [], "errors": [str(exc)]}


def json_exists(path: Path) -> bool:
    """Return whether a JSON file exists."""

    return path.exists() and path.is_file()
