from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ci_dependency_check import check_dependencies
from scripts.ci_docs_check import check_documentation
from scripts.ci_quality_gates import evaluate_quality_gates
from scripts.ci_security_check import scan_repository
from scripts.ci_structure_check import check_structure


def _root(root: Path | None = None) -> Path:
    return root or ROOT


def _check_artifacts(root: Path) -> dict[str, object]:
    warnings: list[str] = []
    errors: list[str] = []
    artifact_roots = [root / "outputs", root / "frontend" / "dist"]
    large_binary_files = []

    for artifact_root in artifact_roots:
        if not artifact_root.exists():
            continue
        for path in artifact_root.rglob("*"):
            if not path.is_file():
                continue
            try:
                if path.stat().st_size > 50 * 1024 * 1024:
                    large_binary_files.append(str(path.relative_to(root)))
            except OSError as exc:
                warnings.append(f"Could not inspect artifact {path}: {exc}")

    if large_binary_files:
        errors.append(f"Large binary artifacts detected: {', '.join(large_binary_files[:5])}")

    return {
        "artifact_safe": not errors,
        "warnings": warnings,
        "errors": errors,
    }


def _observability_compatibility(root: Path) -> dict[str, object]:
    warnings: list[str] = []
    errors: list[str] = []
    try:
        from src.api.api_config import ApiConfig
        from src.api.main import create_app
        from src.observability.observability_health import build_observability_health, get_system_status_summary

        app = create_app(ApiConfig())
        observability_health = build_observability_health(app)
        system_status = get_system_status_summary(app)
        passed = bool(observability_health.get("health_status")) and bool(system_status.get("observability"))
    except Exception as exc:
        passed = False
        errors.append(str(exc))
    return {
        "observability_compatible": passed,
        "warnings": warnings,
        "errors": errors,
    }


def build_pipeline_health(root: Path | None = None) -> dict[str, object]:
    root = _root(root)
    quality_gates = evaluate_quality_gates(root)
    dependency_check = check_dependencies(root)
    docs_check = check_documentation(root)
    structure_check = check_structure(root)
    security_check = scan_repository(root)
    artifact_check = _check_artifacts(root)
    observability_check = _observability_compatibility(root)

    checks = {
        "backend_compile": quality_gates["gates"]["backend_compile"]["passed"],
        "backend_tests": quality_gates["gates"]["backend_tests"]["passed"],
        "frontend_build": quality_gates["gates"]["frontend_build"]["passed"],
        "docker_validation": quality_gates["gates"]["docker_validation"]["passed"],
        "security_scan": quality_gates["gates"]["security_scan"]["passed"],
        "smoke_tests": quality_gates["gates"]["smoke_tests"]["passed"],
        "release_validation": quality_gates["gates"]["release_validation"]["passed"],
        "dependency_validation": dependency_check.get("dependencies_valid", False),
        "docs_validation": docs_check.get("documentation_valid", False),
        "structure_validation": structure_check.get("structure_valid", False),
        "artifact_safety": artifact_check.get("artifact_safe", False) and not security_check.get("errors"),
        "observability_compatibility": observability_check.get("observability_compatible", False),
    }
    warnings = []
    for section in (quality_gates, dependency_check, docs_check, structure_check, security_check, artifact_check, observability_check):
        warnings.extend([str(item) for item in section.get("warnings", [])])

    checks_passed = sum(1 for passed in checks.values() if passed)
    checks_failed = len(checks) - checks_passed
    quality_gate_summary = {
        "quality_gate_status": quality_gates["quality_gate_status"],
        "gates": quality_gates["gates"],
        "checks_passed": quality_gates["checks_passed"],
        "checks_failed": quality_gates["checks_failed"],
        "warnings": quality_gates["warnings"],
    }
    if checks_failed == 0:
        pipeline_health = "healthy"
    elif any(not checks[name] for name in ("backend_compile", "backend_tests", "frontend_build", "docker_validation", "security_scan", "smoke_tests", "release_validation")):
        pipeline_health = "critical"
    else:
        pipeline_health = "warning"
    pipeline_status = "ready" if pipeline_health == "healthy" else "warning" if pipeline_health == "warning" else "blocked"
    score = max(0, 100 - (checks_failed * 8))
    mvp_ready = bool(checks_passed >= 11 and checks["release_validation"] and checks["security_scan"])
    release_ready = bool(checks_failed == 0)
    security_ready = bool(checks["security_scan"] and checks["artifact_safety"])
    return {
        "pipeline_health": pipeline_health,
        "pipeline_health_score": score,
        "pipeline_status": pipeline_status,
        "checks_passed": checks_passed,
        "checks_failed": checks_failed,
        "checks": checks,
        "warnings": warnings,
        "latest_pipeline_run": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": pipeline_status,
            "source": "local_validation",
        },
        "quality_gate_summary": quality_gate_summary,
        "mvp_ready": mvp_ready,
        "release_ready": release_ready,
        "security_ready": security_ready,
    }


def main() -> int:
    result = build_pipeline_health()
    print(json.dumps(result, indent=2))
    return 0 if result["pipeline_health"] == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
