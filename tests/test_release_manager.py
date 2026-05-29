from __future__ import annotations

from pathlib import Path

from src.release.release_manager import ReleaseManager


def test_release_manager_builds_summary(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr("src.release.release_manager.validate_release", lambda app=None, root=None: {"functional_ready": True, "technical_ready": True, "security_ready": True, "deployment_ready": True, "observability_ready": True, "ci_ready": True, "documentation_ready": True, "warnings": [], "errors": [], "functional": {}, "technical": {}, "security": {}, "deployment": {}, "observability": {}, "ci": {}, "documentation": {}, "domains": [{"domain": "security", "status": "pass"}]})
    monkeypatch.setattr("src.release.release_manager.calculate_release_score", lambda summary: {"overall_score": 98, "release_score": 98, "release_status": "ready", "recommendations": [], "factors": {"security": True}, "domain_scores": {"security": 100}})
    monkeypatch.setattr("src.release.release_manager.build_mvp_maturity", lambda summary: {"maturity_score": 96, "maturity_level": "production_ready", "warnings": [], "recommendations": []})
    monkeypatch.setattr("src.release.release_manager.build_release_governance", lambda summary: {"governance_status": "approved", "release_blocked": False, "release_warning": False, "approval_recommended": True, "warnings": [], "blocked_reasons": [], "rules": {}})
    monkeypatch.setattr("src.release.release_manager.build_release_health", lambda app=None, summary=None: {"overall_health": "healthy", "health_score": 97, "warnings": [], "errors": []})
    monkeypatch.setattr("src.release.release_manager.build_release_checklist", lambda summary=None: {"total_checks": 150, "passed": 150, "failed": 0, "warnings": 0, "items": [], "completed": 150, "pending": 0, "blocked": 0, "total": 150})
    monkeypatch.setattr("src.release.release_manager.build_release_audit", lambda app=None, root=None: {"audit_passed": True, "modules": {}})
    monkeypatch.setattr("src.release.release_manager.build_mvp_certification", lambda app=None, root=None, summary=None: {"mvp_certified": True, "production_ready": True, "certification_status": "approved", "version": "1.0.0", "release_score": 98, "maturity_level": "production_ready", "maturity_score": 96, "governance_status": "approved", "warnings": [], "errors": [], "metadata": {}})
    monkeypatch.setattr("src.release.release_manager.build_mvp_acceptance", lambda app=None, root=None, summary=None: {"mvp_ready": True, "release_ready": True, "version": "1.0.0", "acceptance_score": 98, "status": "approved", "certification": {}, "declaration": {}})
    monkeypatch.setattr("src.release.release_manager.build_final_mvp_declaration", lambda app=None, root=None, summary=None: {"mvp_complete": True, "version": "1.0.0", "release_status": "approved", "maturity_level": "production_ready", "production_ready": True, "certified": True, "release_score": 98})
    monkeypatch.setattr("src.release.release_manager.build_executive_summary", lambda summary=None, root=None: "# summary")
    monkeypatch.setattr("src.release.release_manager.build_release_artifact_index", lambda root=None: "# artifacts")
    monkeypatch.setattr("src.release.release_manager.write_release_report", lambda summary=None, root=None: {"generated": True, "path": str(tmp_path / "report.md"), "content": "# report"})
    monkeypatch.setattr("src.release.release_manager.write_executive_summary", lambda summary=None, root=None: {"generated": True, "path": str(tmp_path / "summary.md"), "content": "# summary"})
    monkeypatch.setattr("src.release.release_manager.write_release_artifact_index", lambda root=None: {"generated": True, "path": str(tmp_path / "artifacts.md"), "content": "# artifacts"})

    manager = ReleaseManager()
    summary = manager.build_release_summary()
    package = manager.generate_release_package(root=tmp_path)

    assert summary["mvp_ready"] is True
    assert summary["release_score"] == 98
    assert summary["certification_status"] == "approved"
    assert summary["maturity_level"] == "production_ready"
    assert package["report"]["generated"] is True
