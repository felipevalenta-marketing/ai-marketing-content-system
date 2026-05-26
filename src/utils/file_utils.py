"""Utility helpers for safe markdown file loading and recursive scanning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import unicodedata
from typing import Iterable, List


MARKDOWN_EXTENSION = ".md"


@dataclass(frozen=True)
class MarkdownFileRecord:
    """Represents a discovered markdown file on disk."""

    path: Path
    relative_path: str
    category_path: tuple[str, ...]
    filename_key: str
    folder_key: str


def validate_path(path: str | Path) -> Path:
    """Return a resolved path and raise a clear error when it does not exist."""

    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved}")
    return resolved


def is_markdown_file(path: Path) -> bool:
    """Check whether a file should be treated as markdown."""

    return path.is_file() and path.suffix.lower() == MARKDOWN_EXTENSION


def normalize_key(value: str) -> str:
    """Convert filenames and folder names into stable context keys."""

    cleaned = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = cleaned.strip().lower()
    cleaned = cleaned.replace(MARKDOWN_EXTENSION, "")
    cleaned = cleaned.replace(" ", "_")
    cleaned = cleaned.replace("-", "_")
    cleaned = cleaned.replace("´", "")
    cleaned = cleaned.replace("`", "")
    cleaned = re.sub(r"[^\w/]+", "_", cleaned, flags=re.UNICODE)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")


def read_markdown_file(path: Path) -> str:
    """Read markdown content using UTF-8 with graceful fallback handling."""

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def normalize_markdown_content(content: str) -> str:
    """Normalize markdown text for prompt readability while preserving hierarchy."""

    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    normalized_lines: list[str] = []
    previous_blank = False

    for line in lines:
        stripped = line.rstrip()
        if not stripped.strip():
            if not previous_blank:
                normalized_lines.append("")
            previous_blank = True
            continue

        normalized_lines.append(re.sub(r"[ \t]+", " ", stripped))
        previous_blank = False

    normalized = "\n".join(normalized_lines).strip()
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized


def recursive_markdown_files(root: Path) -> List[MarkdownFileRecord]:
    """Discover markdown files recursively while preserving hierarchy information."""

    records: list[MarkdownFileRecord] = []
    root = root.resolve()
    if not root.exists():
        return records

    for file_path in sorted(root.rglob("*")):
        if not is_markdown_file(file_path):
            continue

        relative_path = file_path.relative_to(root)
        category_path = tuple(
            normalize_key(part)
            for part in relative_path.parts[:-1]
            if part and part != "."
        )
        records.append(
            MarkdownFileRecord(
                path=file_path,
                relative_path=str(relative_path).replace("\\", "/"),
                category_path=category_path,
                filename_key=normalize_key(file_path.stem),
                folder_key=normalize_key(relative_path.parts[0]) if relative_path.parts else "",
            )
        )

    return records


def group_by_key(records: Iterable[MarkdownFileRecord]) -> dict[str, list[MarkdownFileRecord]]:
    """Group records by filename key to help detect duplicates."""

    grouped: dict[str, list[MarkdownFileRecord]] = {}
    for record in records:
        group_key = "/".join((*record.category_path, record.filename_key))
        grouped.setdefault(group_key, []).append(record)
    return grouped
