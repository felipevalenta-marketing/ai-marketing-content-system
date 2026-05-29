"""Validate brand folders and contents safely."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re

from src.brands.brand_profile import build_brand_profile
from src.brands.brand_registry import is_valid_brand_id, normalize_brand_id


SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"bearer\s+[A-Za-z0-9\-\._~\+/=]{8,}", re.IGNORECASE),
    re.compile(r"api[_-]?key\s*[:=]\s*[A-Za-z0-9\-_]{8,}", re.IGNORECASE),
    re.compile(r"password\s*[:=]\s*\S{4,}", re.IGNORECASE),
    re.compile(r"secret\s*[:=]\s*\S{4,}", re.IGNORECASE),
    re.compile(r"token\s*[:=]\s*[A-Za-z0-9\-_\.=]{8,}", re.IGNORECASE),
)


def validate_brand(brand_id: str, root_path: str = "brands") -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    checks: dict[str, Any] = {}
    raw_brand_id = str(brand_id or "").strip()
    brand_key = normalize_brand_id(raw_brand_id)
    root = Path(root_path).expanduser().resolve()
    brand_path = (root / brand_key).resolve()

    checks["brand_id_present"] = bool(raw_brand_id)
    checks["brand_id_safe"] = is_valid_brand_id(raw_brand_id)
    checks["brand_folder_exists"] = brand_path.exists() and brand_path.is_dir()
    checks["within_root"] = str(brand_path).startswith(str(root))
    checks["json_serializable"] = _is_json_serializable({"brand_id": brand_key, "brand_path": str(brand_path)})
    checks["no_hidden_files"] = not any(part.startswith(".") for part in brand_path.parts)
    checks["brand_json_scanned"] = False

    if not checks["brand_id_present"]:
        errors.append("brand_id is required.")
    if not checks["brand_id_safe"]:
        errors.append("brand_id is not filesystem safe.")
    if not checks["brand_folder_exists"]:
        errors.append("Brand folder not found.")
    if not checks["within_root"]:
        errors.append("Brand folder is outside the brands root.")
    if not checks["no_hidden_files"]:
        errors.append("Hidden brand folders are not allowed.")

    profile = build_brand_profile(brand_key, root_path=root_path) if checks["brand_folder_exists"] and checks["within_root"] else {}
    config_path = brand_path / "brand.json"
    if config_path.exists():
        checks["brand_json_scanned"] = True
        try:
            raw_config = config_path.read_text(encoding="utf-8")
            if _contains_secret(raw_config):
                errors.append("Brand configuration appears to contain secrets.")
                checks["no_secrets"] = False
        except Exception as exc:
            errors.append(f"Unable to read brand.json: {exc}")
            checks["brand_json_readable"] = False
    if profile:
        checks["recommended_files_present"] = not profile.get("missing_recommended_files")
        if profile.get("missing_recommended_files"):
            warnings.append("Some recommended brand files are missing.")
        secret_warning = _contains_secret(profile)
        checks["no_secrets"] = not secret_warning
        if secret_warning:
            errors.append("Brand content appears to contain secrets.")
    else:
        checks["recommended_files_present"] = False
        checks["no_secrets"] = True

    return {"valid": not errors, "warnings": warnings, "errors": errors, "checks": checks}


def _contains_secret(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_contains_secret(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    if isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in ("openai_api_key", "api_key", "password", "secret", "token")):
            if "input_tokens" in lower or "output_tokens" in lower or "total_tokens" in lower:
                return False
            return True
        return any(pattern.search(value) for pattern in SECRET_PATTERNS)
    return False


def _is_json_serializable(value: Any) -> bool:
    try:
        json.dumps(value, default=str)
        return True
    except Exception:
        return False
