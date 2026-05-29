from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ci_dependency_check import check_dependencies
from scripts.ci_docs_check import check_documentation
from scripts.ci_quality_gates import evaluate_quality_gates
from scripts.ci_structure_check import check_structure


REQUIRED_FILES = [
    "README.md",
    ".env.example",
    "Dockerfile",
    "docker-compose.yml",
    "deployment/README.md",
    "frontend/package.json",
    "requirements.txt",
]

REQUIRED_DIRS = [
    "src/api",
    "src/auth",
    "src/rbac",
    "src/organizations",
    "src/analytics",
    "src/observability",
    "src/storage",
    "frontend/src",
    "tests",
]

DOC_COMMANDS = [
    "python -m compileall src tests scripts",
    "python -m pytest -p no:cacheprovider",
    "python scripts/production_smoke.py",
    "cd frontend",
    "npm run build",
    "docker compose config",
    "python scripts/ci_security_check.py",
    "python scripts/ci_release_check.py",
]


def _root(root: Path | None = None) -> Path:
    return root or ROOT


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def check_release_readiness(root: Path | None = None) -> dict[str, object]:
    root = _root(root)
    warnings: list[str] = []
    errors: list[str] = []
    dependency_check = check_dependencies(root)
    docs_check = check_documentation(root)
    structure_check = check_structure(root)
    quality_gates = evaluate_quality_gates(root)

    missing_files = [rel for rel in REQUIRED_FILES if not (root / rel).exists()]
    missing_dirs = [rel for rel in REQUIRED_DIRS if not (root / rel).exists()]

    if missing_files:
        errors.append(f"Missing required files: {', '.join(missing_files)}.")
    if missing_dirs:
        errors.append(f"Missing required directories: {', '.join(missing_dirs)}.")

    docs = []
    for rel in ["README.md", "deployment/README.md", "docs/CI_CD.md"]:
        path = root / rel
        if path.exists():
            docs.append(_read_text(path))

    combined_docs = "\n".join(docs).lower()
    for command in DOC_COMMANDS:
        if command.lower() not in combined_docs:
            warnings.append(f"Documentation does not mention: {command}")

    release_factors = {
        "backend_compile": bool(quality_gates.get("gates", {}).get("backend_compile", {}).get("passed")),
        "backend_tests": bool(quality_gates.get("gates", {}).get("backend_tests", {}).get("passed")),
        "frontend_build": bool(quality_gates.get("gates", {}).get("frontend_build", {}).get("passed")),
        "docker_validation": bool(quality_gates.get("gates", {}).get("docker_validation", {}).get("passed")),
        "security_validation": bool(quality_gates.get("gates", {}).get("security_scan", {}).get("passed")),
        "docs_validation": bool(docs_check.get("documentation_valid")),
        "structure_validation": bool(structure_check.get("structure_valid")),
    }
    warnings.extend([str(item) for item in dependency_check.get("warnings", [])])
    warnings.extend([str(item) for item in docs_check.get("warnings", [])])
    warnings.extend([str(item) for item in structure_check.get("warnings", [])])

    score = 100
    for passed in release_factors.values():
        if not passed:
            score -= 15
    if warnings:
        score -= min(10, len(warnings))
    score = max(0, min(100, score))
    if not release_factors["backend_compile"] or not release_factors["backend_tests"] or not release_factors["frontend_build"] or not release_factors["security_validation"]:
        release_status = "blocked"
    elif score >= 95:
        release_status = "ready"
    else:
        release_status = "warning"

    return {
        "success": not errors,
        "release_score": score,
        "release_status": release_status,
        "missing_files": missing_files,
        "missing_dirs": missing_dirs,
        "dependency_validation": dependency_check.get("dependencies_valid", False),
        "documentation_validation": docs_check.get("documentation_valid", False),
        "structure_validation": structure_check.get("structure_valid", False),
        "quality_gate_summary": quality_gates,
        "pipeline_health": "healthy" if quality_gates.get("quality_gate_status") == "passed" else "warning" if quality_gates.get("quality_gate_status") == "warning" else "critical",
        "pipeline_status": "ready" if quality_gates.get("quality_gate_status") == "passed" else "warning" if quality_gates.get("quality_gate_status") == "warning" else "blocked",
        "mvp_ready": bool(quality_gates.get("checks_failed", 1) == 0) and release_status == "ready",
        "release_ready": not errors and release_status == "ready",
        "security_ready": bool(quality_gates.get("gates", {}).get("security_scan", {}).get("passed")),
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    result = check_release_readiness()
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
