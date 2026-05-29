from __future__ import annotations

import json
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ci_dependency_check import check_dependencies
from scripts.ci_docker_check import check_docker
from scripts.ci_docs_check import check_documentation
from scripts.ci_security_check import scan_repository
from scripts.ci_structure_check import check_structure


def _root(root: Path | None = None) -> Path:
    return root or ROOT


def _run_command(args: list[str], cwd: Path | None = None) -> dict[str, object]:
    try:
        completed = subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    except FileNotFoundError:
        if os.name == "nt" and args and args[0] == "npm":
            completed = subprocess.run(["cmd", "/c", *args], cwd=str(cwd) if cwd else None, capture_output=True, text=True)
        else:
            raise
    return {
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
    }


def evaluate_quality_gates(root: Path | None = None) -> dict[str, object]:
    root = _root(root)
    python = sys.executable
    gates: dict[str, dict[str, object]] = {}

    gates["backend_compile"] = _run_command([python, "-m", "compileall", "src", "tests", "scripts"], cwd=root)
    gates["backend_tests"] = _run_command([python, "-m", "pytest", "-p", "no:cacheprovider"], cwd=root)
    gates["frontend_build"] = _run_command(["npm", "run", "build"], cwd=root / "frontend")
    gates["docker_validation"] = check_docker(root)
    gates["security_scan"] = scan_repository(root)
    gates["smoke_tests"] = _run_command([python, "scripts/production_smoke.py"], cwd=root)
    release_docs = check_documentation(root)
    release_structure = check_structure(root)
    release_dependencies = check_dependencies(root)
    release_valid = (
        bool(release_docs.get("documentation_valid"))
        and bool(release_structure.get("structure_valid"))
        and bool(release_dependencies.get("dependencies_valid"))
        and bool(scan_repository(root).get("success"))
    )
    gates["release_validation"] = {
        "passed": release_valid,
        "documentation_valid": release_docs.get("documentation_valid"),
        "structure_valid": release_structure.get("structure_valid"),
        "dependencies_valid": release_dependencies.get("dependencies_valid"),
        "warnings": [
            *release_docs.get("warnings", []),
            *release_structure.get("warnings", []),
            *release_dependencies.get("warnings", []),
        ],
        "errors": [
            *release_docs.get("errors", []),
            *release_structure.get("errors", []),
            *release_dependencies.get("errors", []),
        ],
    }

    normalized: dict[str, dict[str, object]] = {}
    warnings: list[str] = []
    for name, result in gates.items():
        passed = bool(result.get("passed", result.get("success", result.get("release_ready", result.get("dependencies_valid", result.get("documentation_valid", result.get("structure_valid", False)))))))
        normalized[name] = {
            "passed": passed,
            "details": result,
        }
        warnings.extend([str(item) for item in result.get("warnings", [])])

    checks_passed = sum(1 for item in normalized.values() if item["passed"])
    checks_failed = len(normalized) - checks_passed
    quality_gate_status = "passed" if checks_failed == 0 else "warning" if checks_failed <= 2 else "critical"
    return {
        "quality_gate_status": quality_gate_status,
        "gates": normalized,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "warnings": warnings,
    }


def main() -> int:
    result = evaluate_quality_gates()
    print(json.dumps(result, indent=2))
    return 0 if result["quality_gate_status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
