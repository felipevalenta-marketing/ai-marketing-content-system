"""Local JSON storage helpers for organizations data."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import tempfile


def ensure_organizations_root(root: str | Path = "data/organizations") -> Path:
    path = Path(root)
    path.mkdir(parents=True, exist_ok=True)
    for name in ("organizations.json", "teams.json", "memberships.json", "brand_access.json"):
        file_path = path / name
        if not file_path.exists():
            file_path.write_text("{}", encoding="utf-8")
    return path


def load_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return dict(default)
    try:
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return dict(default)
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else dict(default)
    except Exception:
        return dict(default)


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=f".{path.stem}_", suffix=".json", dir=str(path.parent))
    temp_file = Path(temp_path)
    try:
        with open(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
        temp_file.replace(path)
    finally:
        if temp_file.exists() and temp_file != path:
            try:
                temp_file.unlink()
            except Exception:
                pass

