"""Path traversal protection helpers."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from src.reports.markdown_utils import safe_text


def is_safe_path(path: str | Path | Any) -> bool:
    candidate = safe_text(path, limit=512)
    normalized = candidate.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    return not (
        ".." in normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized) is not None
        or "/../" in normalized
        or "/..\\" in normalized
        or any(part.startswith(".") and part not in {".", ".."} for part in parts)
    )


def validate_path(path: str | Path | Any) -> dict[str, Any]:
    safe = is_safe_path(path)
    return {"valid": safe, "warnings": [], "errors": [] if safe else ["Unsafe path detected."], "path": safe_text(path, limit=512)}


def normalize_safe_path(path: str | Path | Any) -> str:
    if not is_safe_path(path):
        raise ValueError("Unsafe path detected.")
    candidate = safe_text(path, limit=512).replace("\\", "/")
    return str(Path(candidate))
