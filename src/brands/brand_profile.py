"""Build brand profile payloads from filesystem-backed brand folders."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import re

from src.brands.brand_defaults import get_brand_defaults, merge_brand_defaults, normalize_brand_defaults
from src.brands.brand_health import build_brand_health
from src.reporting.report_metrics import utc_now_iso


RECOMMENDED_FILES = (
    "audience.md",
    "positioning.md",
    "tone_of_voice.md",
    "content_rules.md",
)

OPTIONAL_FILES = (
    "visual_identity.md",
    "locations.md",
    "market_knowledge.md",
    "platform_rules.md",
    "campaign_rules.md",
    "seo_rules.md",
)


def build_brand_profile(brand_id: str, root_path: str = "brands") -> dict[str, Any]:
    brand_key = str(brand_id or "").strip().lower()
    root = Path(root_path).expanduser().resolve()
    knowledge_path = (root / brand_key).resolve()
    available_files = _discover_markdown_files(knowledge_path)
    file_count = _count_files(knowledge_path)
    markdown_count = len(available_files)
    recommended_files = list(RECOMMENDED_FILES)
    missing_recommended_files = _missing_recommended_files(available_files)
    optional_files = [name for name in OPTIONAL_FILES if name in available_files]
    configuration, configuration_warnings, configuration_errors, configuration_present = _load_brand_configuration(knowledge_path)
    brand_defaults = _build_brand_defaults(brand_key, configuration)
    defaults = merge_brand_defaults(get_brand_defaults(brand_key), brand_defaults)
    display_name = configuration.get("display_name") or defaults.get("display_name") or _display_name(brand_key)
    warnings: list[str] = []
    if not knowledge_path.exists():
        warnings.append("Brand folder not found.")
    if missing_recommended_files:
        warnings.append("Some recommended brand files are missing.")
    warnings.extend(configuration_warnings)
    errors = list(configuration_errors)
    status = _resolve_status(knowledge_path, defaults, configuration, missing_recommended_files, errors)
    validation = {"valid": not errors, "warnings": list(dict.fromkeys(warnings)), "errors": errors, "checks": {"brand_folder_exists": knowledge_path.exists(), "configuration_present": configuration_present, "markdown_readable": bool(available_files)}}
    health = build_brand_health(
        {
            "success": bool(knowledge_path.exists()),
            "brand_id": brand_key,
            "display_name": display_name,
            "status": status,
            "knowledge_path": str(knowledge_path),
            "available_files": available_files,
            "missing_recommended_files": missing_recommended_files,
            "defaults": defaults,
            "configuration_present": configuration_present,
            "markdown_count": markdown_count,
        },
        validation,
    )
    return {
        "success": bool(knowledge_path.exists()),
        "brand_id": brand_key,
        "display_name": display_name,
        "status": status,
        "knowledge_path": str(knowledge_path),
        "available_files": available_files,
        "missing_recommended_files": missing_recommended_files,
        "recommended_files": recommended_files,
        "optional_files": optional_files,
        "defaults": defaults,
        "configuration": configuration,
        "configuration_present": configuration_present,
        "health_score": health.get("health_score", 0),
        "health_status": health.get("health_status", "critical"),
        "health": health,
        "metadata": {
            "root_path": str(root),
            "created_at": utc_now_iso(),
            "modified_at": _modified_at(knowledge_path),
            "file_count": file_count,
            "markdown_count": markdown_count,
            "configuration_present": configuration_present,
        },
        "warnings": list(dict.fromkeys([item for item in warnings if item])),
        "errors": errors or ([] if knowledge_path.exists() else ["Brand folder not found."]),
    }


def _discover_markdown_files(path: Path) -> list[str]:
    if not path.exists():
        return []
    files: list[str] = []
    for md_file in sorted(path.rglob("*.md")):
        if any(part.startswith(".") for part in md_file.parts):
            continue
        try:
            files.append(md_file.relative_to(path).as_posix())
        except Exception:
            files.append(md_file.name)
    return files


def _missing_recommended_files(available_files: list[str]) -> list[str]:
    available_names = {Path(path).name.lower() for path in available_files}
    missing = []
    for name in RECOMMENDED_FILES:
        if name not in available_names:
            missing.append(name)
    return missing


def _count_files(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    for item in path.rglob("*"):
        if item.is_file() and not any(part.startswith(".") for part in item.parts):
            count += 1
    return count


def _load_brand_configuration(path: Path) -> tuple[dict[str, Any], list[str], list[str], bool]:
    config_path = path / "brand.json"
    warnings: list[str] = []
    errors: list[str] = []
    if not config_path.exists():
        return {}, warnings, errors, False
    try:
        raw = config_path.read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            errors.append("brand.json must contain a JSON object.")
            return {}, warnings, errors, True
        configuration: dict[str, Any] = {}
        for key in ("brand_id", "display_name", "default_platform", "default_content_type", "default_campaign_type", "default_language", "default_objective", "default_audience", "default_visual_style", "active"):
            if key in payload and payload[key] not in (None, ""):
                configuration[key] = payload[key]
        if payload.get("brand_id") and str(payload["brand_id"]).strip().lower() != path.name.lower():
            warnings.append("brand.json brand_id does not match the folder name.")
        defaults = payload.get("defaults")
        if isinstance(defaults, dict):
            configuration["defaults"] = normalize_brand_defaults(defaults)
        return configuration, warnings, errors, True
    except Exception as exc:
        errors.append(f"Unable to read brand.json: {exc}")
        return {}, warnings, errors, True


def _build_brand_defaults(brand_id: str, configuration: dict[str, Any]) -> dict[str, Any]:
    defaults = {}
    for key in ("display_name", "default_platform", "default_content_type", "default_campaign_type", "default_language", "default_objective", "default_audience", "default_visual_style"):
        value = configuration.get(key)
        if value not in (None, ""):
            defaults[key] = value
    nested = configuration.get("defaults")
    if isinstance(nested, dict):
        defaults.update({key: value for key, value in nested.items() if value not in (None, "")})
    if "display_name" not in defaults:
        defaults["display_name"] = _display_name(brand_id)
    return defaults


def _resolve_status(path: Path, defaults: dict[str, Any], configuration: dict[str, Any], missing_recommended_files: list[str], errors: list[str]) -> str:
    if not path.exists():
        return "invalid"
    if errors:
        return "invalid"
    if configuration.get("active") is False:
        return "inactive"
    if missing_recommended_files or not defaults:
        return "incomplete"
    return "active"


def _modified_at(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except Exception:
        return utc_now_iso()


def _display_name(brand_id: str) -> str:
    display = re.sub(r"[_\-]+", " ", brand_id).strip()
    return " ".join(part.capitalize() for part in display.split()) if display else brand_id
