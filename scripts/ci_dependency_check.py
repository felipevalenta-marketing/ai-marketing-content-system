from __future__ import annotations

import json
import re
from pathlib import Path


REQ_LINE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+(\[[A-Za-z0-9_,.-]+\])?(\s*(==|>=|<=|~=|!=|>|<)\s*[^;\s]+)?(\s*;.*)?$")


def _root(root: Path | None = None) -> Path:
    return root or Path(__file__).resolve().parents[1]


def _parse_requirements(path: Path) -> list[str]:
    requirements: list[str] = []
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        requirements.append(line)
    return requirements


def _validate_requirements(path: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    if not path.exists():
        errors.append("requirements.txt is missing.")
        return warnings, errors

    for line in _parse_requirements(path):
        if any(token in line for token in ("===", "=>", "=<")):
            errors.append(f"Invalid Python dependency specifier: {line}")
            continue
        if not REQ_LINE_PATTERN.match(line):
            warnings.append(f"Review Python dependency specifier: {line}")
    return warnings, errors


def _validate_package_json(path: Path) -> tuple[list[str], list[str], dict[str, object]]:
    warnings: list[str] = []
    errors: list[str] = []
    metadata: dict[str, object] = {}
    if not path.exists():
        errors.append("frontend/package.json is missing.")
        return warnings, errors, metadata

    data = json.loads(path.read_text(encoding="utf-8"))
    metadata["package_json_present"] = True
    scripts = data.get("scripts", {})
    dependencies = {
        **dict(data.get("dependencies", {})),
        **dict(data.get("devDependencies", {})),
    }
    invalid_versions = []
    for name, version in dependencies.items():
        if not isinstance(version, str) or not version.strip():
            invalid_versions.append(name)
    if invalid_versions:
        errors.append(f"Invalid npm dependency versions for: {', '.join(sorted(invalid_versions))}.")
    if not isinstance(scripts, dict) or not {"dev", "build", "preview"}.issubset(set(scripts)):
        warnings.append("frontend/package.json should define dev, build, and preview scripts.")
    metadata["script_names"] = sorted(str(key) for key in scripts)
    metadata["dependency_names"] = sorted(str(key) for key in dependencies)
    return warnings, errors, metadata


def _validate_package_lock(package_json: Path, package_lock: Path) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    if not package_lock.exists():
        warnings.append("frontend/package-lock.json is missing; CI should fall back to npm install.")
        return warnings, errors

    data = json.loads(package_lock.read_text(encoding="utf-8"))
    root_dependencies = set()
    if package_json.exists():
        package_data = json.loads(package_json.read_text(encoding="utf-8"))
        root_dependencies = set(package_data.get("dependencies", {})) | set(package_data.get("devDependencies", {}))
    lock_dependencies = set()
    lock_root = data.get("packages", {}).get("", {})
    if isinstance(lock_root, dict):
        lock_dependencies = set(lock_root.get("dependencies", {}))
    missing = sorted(root_dependencies - lock_dependencies)
    if missing:
        warnings.append(f"package-lock.json is missing entries for: {', '.join(missing)}.")
    return warnings, errors


def check_dependencies(root: Path | None = None) -> dict[str, object]:
    root = _root(root)
    warnings: list[str] = []
    errors: list[str] = []

    req_warnings, req_errors = _validate_requirements(root / "requirements.txt")
    warnings.extend(req_warnings)
    errors.extend(req_errors)

    pkg_warnings, pkg_errors, metadata = _validate_package_json(root / "frontend" / "package.json")
    warnings.extend(pkg_warnings)
    errors.extend(pkg_errors)

    lock_warnings, lock_errors = _validate_package_lock(root / "frontend" / "package.json", root / "frontend" / "package-lock.json")
    warnings.extend(lock_warnings)
    errors.extend(lock_errors)

    return {
        "dependencies_valid": not errors,
        "success": not errors,
        "warnings": warnings,
        "errors": errors,
        **metadata,
    }


def main() -> int:
    result = check_dependencies()
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
