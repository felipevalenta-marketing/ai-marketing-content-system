from __future__ import annotations

import json
from pathlib import Path


def check_frontend(root: Path | None = None) -> dict[str, object]:
    root = root or Path(__file__).resolve().parents[1]
    frontend_root = root / "frontend"
    package_json = frontend_root / "package.json"
    package_lock = frontend_root / "package-lock.json"
    warnings: list[str] = []
    errors: list[str] = []

    if not package_json.exists():
        errors.append("frontend/package.json is missing.")
        return {"success": False, "warnings": warnings, "errors": errors}

    data = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    required_scripts = {"dev", "build", "preview"}
    missing_scripts = sorted(required_scripts - set(scripts))
    if missing_scripts:
        errors.append(f"Missing frontend scripts: {', '.join(missing_scripts)}.")

    if package_lock.exists():
        warnings.append("package-lock.json detected; use npm ci in CI.")
    else:
        warnings.append("package-lock.json missing; CI should fall back to npm install.")

    return {
        "success": not errors,
        "frontend_root": str(frontend_root),
        "package_json": str(package_json),
        "package_lock_present": package_lock.exists(),
        "scripts": sorted(scripts),
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    result = check_frontend()
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
