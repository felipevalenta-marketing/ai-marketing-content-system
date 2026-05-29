"""Organization registry helpers."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .organization_storage import ensure_organizations_root


SAFE_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UNSAFE_PATH_RE = re.compile(r"(^|[\\/])\.\.([\\/]|$)")


def contains_path_traversal(value: str) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    if text.startswith(("/", "\\")):
        return True
    return UNSAFE_PATH_RE.search(text) is not None or any(token in text for token in ("../", "..\\", "/..", "\\.."))


def normalize_organization_id(value: str) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def is_valid_organization_id(value: str) -> bool:
    if contains_path_traversal(value):
        return False
    raw = str(value or "").strip()
    if not raw:
        return False
    normalized = raw.lower()
    safe_id_re = re.compile(r"^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?$")
    return bool(safe_id_re.fullmatch(normalized))


def normalize_team_id(value: str) -> str:
    return normalize_organization_id(value)


def is_valid_team_id(value: str) -> bool:
    return is_valid_organization_id(value)


def normalize_slug(value: str) -> str:
    return normalize_organization_id(value)


def is_safe_path(root: str | Path, candidate: str | Path) -> bool:
    root_path = Path(root).resolve()
    try:
        candidate_path = Path(candidate).resolve()
    except Exception:
        return False
    return str(candidate_path).startswith(str(root_path))


def discover_organizations(root_path: str = "data/organizations") -> list[dict[str, Any]]:
    ensure_organizations_root(root_path)
    org_file = Path(root_path) / "organizations.json"
    if not org_file.exists():
        return []
    try:
        import json

        payload = json.loads(org_file.read_text(encoding="utf-8")) if org_file.read_text(encoding="utf-8").strip() else {"organizations": []}
    except Exception:
        payload = {"organizations": []}
    return [dict(item) for item in payload.get("organizations", []) if isinstance(item, dict)]


def build_organization_registry(root_path: str = "data/organizations") -> dict[str, Any]:
    organizations = discover_organizations(root_path)
    return {"organizations": organizations, "count": len(organizations)}
