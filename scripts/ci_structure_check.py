from __future__ import annotations

import json
from pathlib import Path


REQUIRED_DIRS = [
    "src/api",
    "src/auth",
    "src/rbac",
    "src/brands",
    "src/organizations",
    "src/configuration",
    "src/analytics",
    "src/observability",
    "src/storage",
    "frontend/src",
    "tests",
]


def check_structure(root: Path | None = None) -> dict[str, object]:
    root = root or Path(__file__).resolve().parents[1]
    warnings: list[str] = []
    errors: list[str] = []
    existing = []

    for rel in REQUIRED_DIRS:
        path = root / rel
        if path.exists() and path.is_dir():
            existing.append(rel)
        else:
            errors.append(f"Missing required project directory: {rel}")

    return {
        "structure_valid": not errors,
        "success": not errors,
        "existing_dirs": existing,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    result = check_structure()
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
