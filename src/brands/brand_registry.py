"""Filesystem-safe brand registry discovery."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from src.brands.brand_defaults import get_brand_defaults
from src.brands.brand_profile import build_brand_profile
from src.reporting.report_metrics import utc_now_iso


BRAND_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


def normalize_brand_id(value: str) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def is_valid_brand_id(value: str) -> bool:
    raw = str(value or "").strip()
    if not raw:
        return False
    if raw.startswith(".") or raw.endswith("."):
        return False
    if Path(raw).is_absolute():
        return False
    if any(part == ".." for part in Path(raw).parts):
        return False
    if "/" in raw or "\\" in raw:
        return False
    brand_id = normalize_brand_id(raw)
    if not brand_id:
        return False
    return bool(BRAND_ID_PATTERN.match(brand_id))


def discover_brands(root_path: str = "brands") -> list[dict[str, Any]]:
    root = Path(root_path).expanduser()
    if not root.exists() or not root.is_dir():
        return []

    brands: list[dict[str, Any]] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        brand_id = normalize_brand_id(child.name)
        if not is_valid_brand_id(brand_id):
            continue
        profile = build_brand_profile(brand_id, root_path=root_path)
        brands.append(
            {
                "brand_id": brand_id,
                "display_name": profile.get("display_name", _display_name(brand_id)),
                "knowledge_path": str(child),
                "status": profile.get("status", "active"),
                "available_files": profile.get("available_files", []),
                "missing_recommended_files": profile.get("missing_recommended_files", []),
                "defaults": profile.get("defaults", get_brand_defaults(brand_id)),
                "metadata": {
                    "path_safe": True,
                    "discovered_at": utc_now_iso(),
                },
            }
        )
    return brands


def build_brand_registry(root_path: str = "brands") -> dict[str, Any]:
    brands = discover_brands(root_path=root_path)
    return {
        "updated_at": utc_now_iso(),
        "root_path": str(Path(root_path).expanduser()),
        "count": len(brands),
        "brands": brands,
    }


def _display_name(brand_id: str) -> str:
    display = brand_id.replace("_", " ").strip()
    return " ".join(part.capitalize() for part in display.split()) if display else brand_id
