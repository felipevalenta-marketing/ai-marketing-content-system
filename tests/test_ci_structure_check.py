from __future__ import annotations

from pathlib import Path

from scripts.ci_structure_check import check_structure


def test_structure_check_passes_with_required_dirs(tmp_path: Path) -> None:
    for rel in [
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
    ]:
        (tmp_path / rel).mkdir(parents=True, exist_ok=True)

    result = check_structure(tmp_path)

    assert result["structure_valid"] is True
    assert result["errors"] == []


def test_structure_check_reports_missing_dirs(tmp_path: Path) -> None:
    result = check_structure(tmp_path)
    assert result["structure_valid"] is False
    assert result["errors"]
