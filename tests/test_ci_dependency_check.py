from __future__ import annotations

import json
from pathlib import Path

from scripts.ci_dependency_check import check_dependencies


def test_dependency_check_passes_with_valid_files(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("openai\npytest\n", encoding="utf-8")
    frontend = tmp_path / "frontend"
    frontend.mkdir(parents=True, exist_ok=True)
    (frontend / "package.json").write_text(
        json.dumps(
            {
                "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"},
                "dependencies": {"react": "^18.3.1"},
                "devDependencies": {"vite": "^5.4.2"},
            }
        ),
        encoding="utf-8",
    )
    (frontend / "package-lock.json").write_text(
        json.dumps({"packages": {"": {"dependencies": {"react": "^18.3.1", "vite": "^5.4.2"}}}}),
        encoding="utf-8",
    )

    result = check_dependencies(tmp_path)

    assert result["dependencies_valid"] is True
    assert result["errors"] == []


def test_dependency_check_reports_missing_files(tmp_path: Path) -> None:
    result = check_dependencies(tmp_path)
    assert result["dependencies_valid"] is False
    assert any("requirements.txt" in error for error in result["errors"])
