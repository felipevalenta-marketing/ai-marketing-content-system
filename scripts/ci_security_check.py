from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
}

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
    ".css",
    ".html",
    ".sh",
    ".ps1",
    ".cfg",
}

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

SECRET_ASSIGNMENT_PATTERNS = {
    "OPENAI_API_KEY": re.compile(r"^\s*OPENAI_API_KEY\s*=\s*(.+?)\s*$", re.IGNORECASE),
    "JWT_SECRET_KEY": re.compile(r"^\s*JWT_SECRET_KEY\s*=\s*(.+?)\s*$", re.IGNORECASE),
    "API_KEY": re.compile(r"^\s*api_key\s*=\s*(.+?)\s*$", re.IGNORECASE),
    "PASSWORD": re.compile(r"^\s*password\s*=\s*(.+?)\s*$", re.IGNORECASE),
}

SK_KEY_PATTERN = re.compile(r"\bsk-[A-Za-z0-9]{16,}\b")
BEARER_PATTERN = re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}\b")
PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
TEMP_FILE_SUFFIXES = {".tmp", ".temp", ".bak", ".swp", ".orig", "~"}
MAX_BINARY_SIZE = 50 * 1024 * 1024


def _is_skippable(path: Path) -> bool:
    parts = set(path.parts)
    return any(part in SKIP_DIRS for part in parts)


def _is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {".env", ".env.example", "Dockerfile", "docker-compose.yml", "docker-compose.override.yml"}


def _has_placeholder(value: str) -> bool:
    normalized = value.strip().strip('"').strip("'").lower()
    return any(marker in normalized for marker in ALLOWLIST_VALUES)


def _tracked_files(root: Path) -> list[Path]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return [path for path in root.rglob("*") if path.is_file()]

    files = [root / entry for entry in completed.stdout.split("\0") if entry]
    return [path for path in files if path.exists() and path.is_file()]


def _artifact_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for rel in [root / "outputs", root / "frontend" / "dist"]:
        if not rel.exists():
            continue
        for path in rel.rglob("*"):
            if path.is_file():
                files.append(path)
    return files


def _scan_paths(root: Path, paths: list[Path], warnings: list[str], errors: list[str], scanned_files: list[int], respect_skip_dirs: bool = True) -> None:
    for path in paths:
        try:
            relative = path.relative_to(root)
        except Exception:
            relative = path
        if respect_skip_dirs and _is_skippable(relative):
            continue
        if path.name == ".env":
            errors.append(f"Committed .env file detected: {relative.as_posix()}")
            continue
        if relative.name.startswith(".env") and relative.name != ".env.example":
            errors.append(f"Suspicious env file detected: {relative.as_posix()}")
            continue
        if path.suffix.lower() in {".pyc", ".pyo"} or "__pycache__" in relative.parts:
            errors.append(f"Compiled cache file detected: {relative.as_posix()}")
            continue
        if any(str(path).lower().endswith(suffix) for suffix in TEMP_FILE_SUFFIXES):
            errors.append(f"Temporary file detected: {relative.as_posix()}")
            continue
        if not _is_text_file(path):
            try:
                if path.stat().st_size > MAX_BINARY_SIZE:
                    errors.append(f"Large binary file detected: {relative.as_posix()}")
            except Exception:
                warnings.append(f"Could not inspect file size for {relative.as_posix()}.")
            continue

        scanned_files[0] += 1
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
                if match := SECRET_ASSIGNMENT_PATTERNS["JWT_SECRET_KEY"].match(stripped):
                    if not _has_placeholder(match.group(1)):
                        errors.append(f"Potential JWT_SECRET_KEY secret in {relative.as_posix()}:{line_number}")
                if match := SECRET_ASSIGNMENT_PATTERNS["API_KEY"].match(stripped):
                    if not _has_placeholder(match.group(1)):
                        errors.append(f"Potential api_key secret in {relative.as_posix()}:{line_number}")
                if match := SECRET_ASSIGNMENT_PATTERNS["PASSWORD"].match(stripped):
                    if not _has_placeholder(match.group(1)):
                        errors.append(f"Potential password secret in {relative.as_posix()}:{line_number}")

            if SK_KEY_PATTERN.search(line):
                errors.append(f"Potential OpenAI-style secret key in {relative.as_posix()}:{line_number}")
            if BEARER_PATTERN.search(line):
                errors.append(f"Potential bearer token in {relative.as_posix()}:{line_number}")
            if PRIVATE_KEY_PATTERN.search(line):
                errors.append(f"Private key block detected in {relative.as_posix()}:{line_number}")


def scan_repository(root: Path | None = None) -> dict[str, object]:
    root = root or Path(__file__).resolve().parents[1]
    warnings: list[str] = []
    errors: list[str] = []
    scanned_files = [0]

    _scan_paths(root, _tracked_files(root), warnings, errors, scanned_files, respect_skip_dirs=True)
    _scan_paths(root, _artifact_files(root), warnings, errors, scanned_files, respect_skip_dirs=False)

    return {
        "success": not errors,
        "scanned_files": scanned_files[0],
        "hygiene_violations": len(errors),
        "artifact_safe": not errors,
        "warnings": warnings,
        "errors": errors,
    }


def main() -> int:
    result = scan_repository()
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
