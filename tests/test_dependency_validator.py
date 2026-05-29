from __future__ import annotations

import json
from pathlib import Path

from src.security.dependency_validator import validate_dependencies


def test_dependency_validator_accepts_basic_project(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("fastapi==0.1.0\n", encoding="utf-8")
    frontend = tmp_path / "frontend"
    frontend.mkdir(parents=True, exist_ok=True)
    (frontend / "package.json").write_text(
        json.dumps(
            {
                "name": "frontend",
                "scripts": {"build": "vite build"},
                "dependencies": {"react": "^18.0.0"},
                "devDependencies": {"typescript": "^5.0.0"},
            }
        ),
        encoding="utf-8",
    )
    result = validate_dependencies(tmp_path)
    assert result["dependencies_valid"] is True


def test_dependency_validator_reports_missing_files(tmp_path: Path) -> None:
    result = validate_dependencies(tmp_path)
    assert result["dependencies_valid"] is False
    assert result["errors"]

