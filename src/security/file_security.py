"""File name and extension validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from src.reports.markdown_utils import safe_text
from .path_security import is_safe_path


ALLOWED_EXTENSIONS = {
    ".json",
    ".md",
    ".txt",
    ".csv",
    ".tsv",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".log",
}
BLOCKED_EXTENSIONS = {
    ".exe",
    ".dll",
    ".bat",
    ".cmd",
    ".sh",
    ".ps1",
    ".js",
    ".mjs",
    ".pyo",
    ".pyc",
}


def sanitize_file_name(value: Any) -> str:
    text = safe_text(value, limit=240).strip().replace("\\", "_").replace("/", "_").replace("..", "_")
    text = re.sub(r"[^a-zA-Z0-9._-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("._-") or "file"


def is_allowed_extension(extension: str) -> bool:
    normalized = f".{str(extension or '').strip().lstrip('.').lower()}"
    return normalized in ALLOWED_EXTENSIONS and normalized not in BLOCKED_EXTENSIONS


def validate_file_name(name: str | Path | Any) -> dict[str, Any]:
    candidate = safe_text(name, limit=240)
    safe_name = sanitize_file_name(candidate)
    valid = bool(candidate) and safe_name == candidate.replace(" ", "_").replace("\\", "_").replace("/", "_")
    if candidate.startswith(".") and candidate not in {".env.example"}:
        valid = False
    if candidate.lower().endswith(tuple(BLOCKED_EXTENSIONS)):
        valid = False
    return {"valid": valid, "warnings": [], "errors": [] if valid else ["Unsafe file name."], "file_name": safe_name}


def validate_file_path(path: str | Path | Any, *, allowed_extensions: set[str] | None = None) -> dict[str, Any]:
    candidate = safe_text(path, limit=512)
    if not is_safe_path(candidate):
        return {"valid": False, "warnings": [], "errors": ["Unsafe file path."], "file_path": candidate}
    extension = Path(candidate).suffix.lower()
    allowed = {ext.lower() for ext in (allowed_extensions or ALLOWED_EXTENSIONS)}
    valid = extension in allowed and extension not in BLOCKED_EXTENSIONS
    return {"valid": valid, "warnings": [], "errors": [] if valid else ["Unsafe file extension."], "file_path": candidate}
