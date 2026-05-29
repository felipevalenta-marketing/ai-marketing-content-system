from __future__ import annotations

from pathlib import Path

from src.release import release_validator


def test_release_validator_combines_section_results(monkeypatch) -> None:
    monkeypatch.setattr(release_validator, "validate_functional", lambda app=None, root=None: {"functional_ready": True, "modules": [{"module": "api", "status": "pass"}], "warnings": [], "errors": []})
    monkeypatch.setattr(release_validator, "validate_technical", lambda root=None: {"technical_ready": True, "pipeline_health": {}, "warnings": [], "errors": []})
    monkeypatch.setattr(release_validator, "validate_security", lambda root=None, app=None: {"security_ready": True, "security_score": 97, "baseline_ready": True, "baseline_score": 100, "warnings": [], "errors": []})
    monkeypatch.setattr(release_validator, "validate_deployment", lambda root=None: {"deployment_ready": True, "missing": [], "warnings": [], "errors": []})
    monkeypatch.setattr(release_validator, "validate_observability", lambda app=None: {"observability_ready": True, "health": {}, "warnings": [], "errors": []})
    monkeypatch.setattr(release_validator, "validate_ci", lambda root=None: {"ci_ready": True, "pipeline_health": {}, "quality_gates": {}, "warnings": [], "errors": []})
    monkeypatch.setattr(release_validator, "validate_documentation", lambda root=None: {"documentation_ready": True, "documentation": {}, "warnings": [], "errors": []})

    result = release_validator.validate_release()

    assert result["functional_ready"] is True
    assert result["technical_ready"] is True
    assert result["security_ready"] is True
    assert result["deployment_ready"] is True
    assert result["observability_ready"] is True
    assert result["ci_ready"] is True
    assert result["documentation_ready"] is True
    assert result["domains"]
    assert release_validator.list_domains()
    assert release_validator.get_domain_status("security", summary=result)["status"] == "pass"


def test_release_documentation_validation_detects_present_docs(tmp_path: Path) -> None:
    for rel in [
        "README.md",
        "deployment/README.md",
        "docs/CI_CD.md",
        "docs/MVP_ACCEPTANCE.md",
        "docs/RELEASE_NOTES.md",
        "docs/DEPLOYMENT_GUIDE.md",
        "docs/MVP_EXECUTIVE_SUMMARY.md",
        "docs/RELEASE_ARTIFACTS.md",
    ]:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("ok", encoding="utf-8")

    result = release_validator.validate_documentation(tmp_path)
    assert result["documentation_ready"] is True
    assert result["errors"] == []


def test_release_deployment_validation_detects_missing_files(tmp_path: Path) -> None:
    result = release_validator.validate_deployment(tmp_path)
    assert result["deployment_ready"] is False
    assert result["missing"]
