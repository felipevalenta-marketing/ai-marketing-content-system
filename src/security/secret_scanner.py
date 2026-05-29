"""Repository secret scanner."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json
import re
import subprocess


TEXT_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".txt",
    ".toml",
    ".ini",
    ".cfg",
    ".sh",
    ".ps1",
    ".html",
    ".css",
}

TEMP_FILE_SUFFIXES = {".tmp", ".temp", ".bak", ".swp", ".orig", "~"}

ALLOWLIST_VALUES = {
    "replace_with_secure_random_value",
    "your_openai_api_key_here",
    "your_jwt_secret_key",
    "dummy_ci_key_do_not_use",
    "dummy_ci_jwt_secret_for_tests_only",
    "placeholder",
    "change_me",
    "change-this",
    "example",
}

ALLOWLISTED_FINDINGS = {
    ("tests/test_ci_security_check.py", "sk_key"),
}

SECRET_ASSIGNMENT_PATTERNS = {
    "OPENAI_API_KEY": re.compile(r"^\s*OPENAI_API_KEY\s*=\s*(.+?)\s*$", re.IGNORECASE),
    "JWT_SECRET_KEY": re.compile(r"^\s*JWT_SECRET_KEY\s*=\s*(.+?)\s*$", re.IGNORECASE),
    "API_KEY": re.compile(r"^\s*api_key\s*=\s*(.+?)\s*$", re.IGNORECASE),
    "PASSWORD": re.compile(r"^\s*password\s*=\s*(.+?)\s*$", re.IGNORECASE),
}

SK_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9]{16,}\b")
BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b")
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")


def _has_placeholder(value: str) -> bool:
    normalized = value.strip().strip('"').strip("'").lower()
    return any(marker in normalized for marker in ALLOWLIST_VALUES)


def _tracked_files(root: Path) -> list[Path]:
    try:
        completed = subprocess.run(["git", "-C", str(root), "ls-files"], check=True, capture_output=True, text=True)
    except Exception:
        ignored_parts = {".git", ".venv", "venv", "node_modules", ".pytest_cache", "__pycache__", "dist"}
        return [
            path
            for path in root.rglob("*")
            if path.is_file() and not any(part in ignored_parts for part in path.relative_to(root).parts)
        ]
    return [root / entry.strip() for entry in completed.stdout.splitlines() if entry.strip()]


def _is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {".env", ".env.example", "Dockerfile", "docker-compose.yml", "docker-compose.override.yml"}


def scan_repository(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    warnings: list[str] = []
    errors: list[str] = []
    findings: list[dict[str, Any]] = []
    scanned_files = 0
    for path in _tracked_files(root):
        if not path.exists() or not path.is_file():
            continue
        try:
            relative = path.relative_to(root)
        except Exception:
            relative = path
        if any(part in {".git", ".venv", "venv"} for part in relative.parts):
            continue
        if any(part in {"node_modules", "dist", "__pycache__"} for part in relative.parts) or path.suffix.lower() in {".pyc", ".pyo"}:
            errors.append(f"Committed build or cache artifact detected: {relative.as_posix()}")
            findings.append({"path": relative.as_posix(), "issue": "build_or_cache_artifact", "severity": "critical"})
            continue
        if any(str(path).lower().endswith(suffix) for suffix in TEMP_FILE_SUFFIXES):
            errors.append(f"Temporary file detected: {relative.as_posix()}")
            findings.append({"path": relative.as_posix(), "issue": "temporary_file", "severity": "critical"})
            continue
        if path.name == ".env":
            errors.append(f"Committed .env file detected: {relative.as_posix()}")
            findings.append({"path": relative.as_posix(), "issue": "env_file", "severity": "critical"})
            continue
        if relative.name.startswith(".env") and relative.name != ".env.example":
            errors.append(f"Suspicious env file detected: {relative.as_posix()}")
            findings.append({"path": relative.as_posix(), "issue": "env_file", "severity": "critical"})
            continue
        if path.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in relative.parts:
            errors.append(f"Compiled cache file detected: {relative.as_posix()}")
            findings.append({"path": relative.as_posix(), "issue": "pycache", "severity": "critical"})
            continue
        if not _is_text_file(path):
            try:
                if path.stat().st_size > 50 * 1024 * 1024:
                    errors.append(f"Large binary file detected: {relative.as_posix()}")
                    findings.append({"path": relative.as_posix(), "issue": "large_binary", "severity": "warning"})
            except Exception:
                warnings.append(f"Could not inspect file size for {relative.as_posix()}.")
            continue
        scanned_files += 1
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            warnings.append(f"Skipped unreadable file {relative.as_posix()}: {exc}")
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            config_like = path.name.startswith(".env") or path.suffix.lower() in {".yml", ".yaml", ".json", ".toml", ".ini", ".cfg"}
            if config_like:
                if match := SECRET_ASSIGNMENT_PATTERNS["OPENAI_API_KEY"].match(stripped):
                    if not _has_placeholder(match.group(1)):
                        errors.append(f"Potential OPENAI_API_KEY secret in {relative.as_posix()}:{line_number}")
                        findings.append({"path": relative.as_posix(), "line": line_number, "issue": "openai_api_key", "severity": "critical"})
                if match := SECRET_ASSIGNMENT_PATTERNS["JWT_SECRET_KEY"].match(stripped):
                    if not _has_placeholder(match.group(1)):
                        errors.append(f"Potential JWT_SECRET_KEY secret in {relative.as_posix()}:{line_number}")
                        findings.append({"path": relative.as_posix(), "line": line_number, "issue": "jwt_secret_key", "severity": "critical"})
                if match := SECRET_ASSIGNMENT_PATTERNS["API_KEY"].match(stripped):
                    if not _has_placeholder(match.group(1)):
                        errors.append(f"Potential api_key secret in {relative.as_posix()}:{line_number}")
                        findings.append({"path": relative.as_posix(), "line": line_number, "issue": "api_key", "severity": "critical"})
                if match := SECRET_ASSIGNMENT_PATTERNS["PASSWORD"].match(stripped):
                    if not _has_placeholder(match.group(1)):
                        errors.append(f"Potential password secret in {relative.as_posix()}:{line_number}")
                        findings.append({"path": relative.as_posix(), "line": line_number, "issue": "password", "severity": "critical"})
            if SK_KEY_PATTERN.search(line):
                finding_key = (relative.as_posix(), "sk_key")
                if finding_key in ALLOWLISTED_FINDINGS:
                    continue
                errors.append(f"Potential OpenAI-style secret key in {relative.as_posix()}:{line_number}")
                findings.append({"path": relative.as_posix(), "line": line_number, "issue": "sk_key", "severity": "critical"})
            if BEARER_PATTERN.search(line):
                errors.append(f"Potential bearer token in {relative.as_posix()}:{line_number}")
                findings.append({"path": relative.as_posix(), "line": line_number, "issue": "bearer_token", "severity": "critical"})
            if PRIVATE_KEY_PATTERN.search(line):
                errors.append(f"Private key block detected in {relative.as_posix()}:{line_number}")
                findings.append({"path": relative.as_posix(), "line": line_number, "issue": "private_key", "severity": "critical"})
    return {
        "success": not errors,
        "scanned_files": scanned_files,
        "findings": findings,
        "hygiene_violations": len(errors),
        "artifact_safe": not errors,
        "warnings": warnings,
        "errors": errors,
    }


def build_findings_report(root: Path | None = None) -> dict[str, Any]:
    result = scan_repository(root=root)
    return {
        "security_findings": result.get("findings", []),
        "count": len(result.get("findings", [])),
        "warnings": result.get("warnings", []),
        "errors": result.get("errors", []),
        "success": result.get("success", False),
    }
