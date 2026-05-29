from __future__ import annotations

import json
from pathlib import Path


REQUIRED_DOCS = [
    "README.md",
    "deployment/README.md",
    "docs/CI_CD.md",
]


def check_documentation(root: Path | None = None) -> dict[str, object]:
    root = root or Path(__file__).resolve().parents[1]
    warnings: list[str] = []
    errors: list[str] = []
    existing = []

    for rel in REQUIRED_DOCS:
        path = root / rel
        if path.exists():
            existing.append(rel)
        else:
            errors.append(f"Missing required documentation file: {rel}")

    return {
        "documentation_valid": not errors,
        "success": not errors,
        "existing_docs": existing,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    result = check_documentation()
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
