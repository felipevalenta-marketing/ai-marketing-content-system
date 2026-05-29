"""Dependency validation helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re


VALID_VERSION_PATTERN = re.compile(r"^[~^]?\d+(?:\.\d+){0,2}(?:[a-zA-Z0-9\-.+]+)?$")


def _validate_requirements(path: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    if not path.exists():
        errors.append("requirements.txt is missing.")
        return warnings, errors
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "==" in stripped:
            name, version = stripped.split("==", 1)
            if not name.strip() or not VALID_VERSION_PATTERN.match(version.strip()):
                errors.append(f"Invalid dependency version in requirements.txt:{line_number}")
        elif any(operator in stripped for operator in (">=", "<=", "~=", "!=")):
            warnings.append(f"Flexible dependency pin in requirements.txt:{line_number}")
    return warnings, errors


def _validate_package_json(path: Path) -> tuple[list[str], list[str], dict[str, Any]]:
    warnings: list[str] = []
    errors: list[str] = []
    metadata: dict[str, Any] = {}
    if not path.exists():
        errors.append("frontend/package.json is missing.")
        return warnings, errors, metadata
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"package.json is invalid JSON: {exc}")
        return warnings, errors, metadata
    metadata["scripts"] = sorted(list((payload.get("scripts") or {}).keys()))
    for section in ("dependencies", "devDependencies"):
        dependencies = payload.get(section) or {}
        if not isinstance(dependencies, dict):
            errors.append(f"{section} must be an object.")
            continue
        for name, version in dependencies.items():
            version_text = str(version).strip()
            if not version_text:
                errors.append(f"Missing version for {name} in {section}.")
            elif version_text != "*" and not VALID_VERSION_PATTERN.match(version_text.lstrip("^~")) and not version_text.startswith("file:"):
                warnings.append(f"Potentially invalid version for {name} in {section}.")
    return warnings, errors, metadata


def validate_dependencies(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    requirements_path = root / "requirements.txt"
    package_json_path = root / "frontend" / "package.json"
    package_lock_path = root / "frontend" / "package-lock.json"
    warnings, errors = _validate_requirements(requirements_path)
    package_warnings, package_errors, package_metadata = _validate_package_json(package_json_path)
    warnings.extend(package_warnings)
    errors.extend(package_errors)
    if package_lock_path.exists() and package_json_path.exists():
        warnings.append("package-lock.json present; ensure it stays in sync with package.json.")
    return {
        "dependencies_valid": not errors,
        "warnings": warnings,
        "errors": errors,
        "metadata": {
            "requirements_exists": requirements_path.exists(),
            "package_json_exists": package_json_path.exists(),
            "package_lock_exists": package_lock_path.exists(),
            **package_metadata,
        },
    }

