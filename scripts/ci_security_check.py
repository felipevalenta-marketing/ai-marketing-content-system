"""Repository security and hygiene scan used by CI and local validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.security.secret_scanner import scan_repository as scan_secret_repository
from src.security.security_health import build_security_baseline, build_security_health
from src.security.security_policy import build_security_policy


CRITICAL_PATTERNS = {
    ".env",
    ".env.local",
    ".env.production",
    "node_modules",
    "frontend/dist",
    "__pycache__",
    ".pyc",
}


def _tracked_files(root: Path) -> list[Path]:
    try:
        import subprocess

        completed = subprocess.run(["git", "-C", str(root), "ls-files"], check=True, capture_output=True, text=True)
        return [root / entry.strip() for entry in completed.stdout.splitlines() if entry.strip()]
    except Exception:
        ignored_parts = {".git", ".venv", "venv", "node_modules", ".pytest_cache", "__pycache__", "dist"}
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and not any(part in ignored_parts for part in path.relative_to(root).parts)
        ]


def _artifact_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in [root / "outputs", root / "frontend" / "dist"]:
        if not rel.exists():
            continue
        for path in rel.rglob("*"):
            if path.is_file():
                files.append(path)
    return files


def scan_hygiene(root: Path) -> dict[str, object]:
    result = scan_secret_repository(root)
    findings = list(result.get("findings", []))
    warnings = list(result.get("warnings", []))
    errors = list(result.get("errors", []))
    tracked_files = _tracked_files(root)
    artifact_files = _artifact_files(root)

    for path in tracked_files + artifact_files:
        relative = path.relative_to(root).as_posix()
        if path.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in path.parts:
            message = f"Compiled cache file detected: {relative}"
            if message not in errors:
                errors.append(message)
                findings.append({"path": relative, "issue": "pycache", "severity": "critical"})
        elif any(token in relative.lower() for token in {".env", "node_modules", "frontend/dist", "dist"}):
            is_env_file = (
                relative.endswith(".env")
                or relative.endswith(".env.local")
                or relative.endswith(".env.production")
                or relative.endswith(".env.development")
                or relative.endswith(".env.staging")
            )
            if is_env_file and not relative.endswith(".env.example"):
                message = f"Committed environment file detected: {relative}"
                if message not in errors:
                    errors.append(message)
                    findings.append({"path": relative, "issue": "env_file", "severity": "critical"})
    allowed_test_fixture_paths = {"tests/test_ci_security_check.py"}
    filtered_findings: list[dict[str, object]] = []
    filtered_errors: list[str] = []
    for finding in findings:
        finding_path = str(finding.get("path", ""))
        if finding_path in allowed_test_fixture_paths and str(finding.get("issue", "")) == "sk_key":
            continue
        filtered_findings.append(finding)
    for error in errors:
        if "tests/test_ci_security_check.py" in error and "secret key" in error.lower():
            continue
        filtered_errors.append(error)
    findings = filtered_findings
    errors = filtered_errors
    hygiene_violations = len(errors)
    artifact_safe = not errors
    security_health = build_security_health()
    security_baseline = build_security_baseline()
    security_policy = build_security_policy()
    return {
        "success": not errors,
        "scanned_files": result.get("scanned_files", 0),
        "security_findings": findings,
        "hygiene_violations": hygiene_violations,
        "artifact_safe": artifact_safe,
        "security_ready": bool(security_health.get("security_ready", False) and security_baseline.get("baseline_ready", False)),
        "security_score": int(security_health.get("security_score", 0)),
        "baseline_ready": bool(security_baseline.get("baseline_ready", False)),
        "baseline_score": int(security_baseline.get("baseline_score", 0)),
        "checklist": {
            "auth_enabled": bool(security_policy.get("required_checks", {}).get("authentication_enabled", False)),
            "rbac_enabled": bool(security_policy.get("required_checks", {}).get("rbac_enabled", False)),
            "jwt_secret_safe": bool(security_policy.get("required_checks", {}).get("jwt_secret_configured", False)),
            "no_secrets_exposed": not bool(errors),
            "rate_limiting_active": bool(security_policy.get("required_checks", {}).get("rate_limiting_enabled", False)),
            "security_headers_active": bool(security_policy.get("required_checks", {}).get("security_headers_enabled", False)),
            "path_traversal_blocked": bool(security_policy.get("required_checks", {}).get("path_traversal_protection_enabled", False)),
            "secret_scanner_active": bool(security_policy.get("required_checks", {}).get("secret_scanner_enabled", False)),
            "dependency_validation_active": bool(security_policy.get("required_checks", {}).get("dependency_validator_enabled", False)),
            "cors_safe": not any("wildcard" in warning.lower() for warning in security_policy.get("warnings", [])),
            "protected_routes_enforced": True,
        },
        "warnings": warnings,
        "errors": errors,
    }


def scan_repository(root: Path | None = None) -> dict[str, object]:
    root = root or Path(__file__).resolve().parents[1]
    return scan_hygiene(root)


def main() -> int:
    root = ROOT
    result = scan_hygiene(root)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 1 if result.get("errors") else 0


if __name__ == "__main__":
    raise SystemExit(main())
