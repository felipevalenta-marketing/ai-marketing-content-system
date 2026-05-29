from __future__ import annotations

from pathlib import Path

from scripts import ci_release_check


def _write_required_layout(root: Path) -> None:
    for rel in [
        "README.md",
        ".env.example",
        "Dockerfile",
        "docker-compose.yml",
        "deployment/README.md",
        "frontend/package.json",
        "requirements.txt",
        "docs/CI_CD.md",
        "src/api/__init__.py",
        "src/auth/__init__.py",
        "src/rbac/__init__.py",
        "src/organizations/__init__.py",
        "src/analytics/__init__.py",
        "src/observability/__init__.py",
        "src/storage/__init__.py",
        "frontend/src/main.tsx",
        "tests/test_placeholder.py",
    ]:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.suffix:
            target.write_text("placeholder", encoding="utf-8")
        else:
            target.mkdir(parents=True, exist_ok=True)

    (root / "README.md").write_text(
        "\n".join(
            [
                "python -m compileall src tests scripts",
                "python -m pytest -p no:cacheprovider",
                "python scripts/production_smoke.py",
                "docker compose config",
                "docker build -t ai-marketing-content-system:test .",
                "python scripts/ci_security_check.py",
                "python scripts/ci_release_check.py",
            ]
        ),
        encoding="utf-8",
    )
    (root / "deployment/README.md").write_text(
        "\n".join(
            [
                "python scripts/check_env.py",
                "python scripts/production_smoke.py",
                "docker compose config",
            ]
        ),
        encoding="utf-8",
    )
    (root / "docs/CI_CD.md").write_text(
        "\n".join(
            [
                "python -m compileall src tests scripts",
                "python -m pytest -p no:cacheprovider",
                "python scripts/production_smoke.py",
                "cd frontend",
                "npm run build",
                "docker compose config",
                "python scripts/ci_security_check.py",
                "python scripts/ci_release_check.py",
            ]
        ),
        encoding="utf-8",
    )


def test_release_check_passes_when_required_files_exist(tmp_path: Path, monkeypatch) -> None:
    _write_required_layout(tmp_path)
    monkeypatch.setattr(
        ci_release_check,
        "evaluate_quality_gates",
        lambda root: {
            "quality_gate_status": "passed",
            "gates": {
                "backend_compile": {"passed": True},
                "backend_tests": {"passed": True},
                "frontend_build": {"passed": True},
                "docker_validation": {"passed": True},
                "security_scan": {"passed": True},
                "smoke_tests": {"passed": True},
                "release_validation": {"passed": True},
            },
            "checks_passed": 7,
            "checks_failed": 0,
            "warnings": [],
        },
    )
    monkeypatch.setattr(ci_release_check, "check_dependencies", lambda root: {"dependencies_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_release_check, "check_documentation", lambda root: {"documentation_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_release_check, "check_structure", lambda root: {"structure_valid": True, "warnings": [], "errors": []})

    result = ci_release_check.check_release_readiness(tmp_path)

    assert result["success"] is True
    assert result["release_ready"] is True
    assert result["release_status"] == "ready"
    assert result["release_score"] >= 95
    assert result["mvp_ready"] is True
    assert result["quality_gate_summary"]["quality_gate_status"] == "passed"
    assert result["errors"] == []


def test_release_check_reports_missing_required_files(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("placeholder", encoding="utf-8")
    monkeypatch.setattr(
        ci_release_check,
        "evaluate_quality_gates",
        lambda root: {
            "quality_gate_status": "warning",
            "gates": {
                "backend_compile": {"passed": True},
                "backend_tests": {"passed": True},
                "frontend_build": {"passed": True},
                "docker_validation": {"passed": True},
                "security_scan": {"passed": True},
                "smoke_tests": {"passed": True},
                "release_validation": {"passed": True},
            },
            "checks_passed": 7,
            "checks_failed": 0,
            "warnings": [],
        },
    )
    monkeypatch.setattr(ci_release_check, "check_dependencies", lambda root: {"dependencies_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_release_check, "check_documentation", lambda root: {"documentation_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_release_check, "check_structure", lambda root: {"structure_valid": True, "warnings": [], "errors": []})

    result = ci_release_check.check_release_readiness(tmp_path)
    assert result["success"] is False
    assert result["missing_files"]
