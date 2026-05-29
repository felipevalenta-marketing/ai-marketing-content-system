from __future__ import annotations

from scripts import ci_pipeline_health


def test_pipeline_health_aggregates_quality_gates(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        ci_pipeline_health,
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
    monkeypatch.setattr(ci_pipeline_health, "check_dependencies", lambda root: {"dependencies_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_pipeline_health, "check_documentation", lambda root: {"documentation_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_pipeline_health, "check_structure", lambda root: {"structure_valid": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_pipeline_health, "scan_repository", lambda root: {"success": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_pipeline_health, "_check_artifacts", lambda root: {"artifact_safe": True, "warnings": [], "errors": []})
    monkeypatch.setattr(ci_pipeline_health, "_observability_compatibility", lambda root: {"observability_compatible": True, "warnings": [], "errors": []})

    result = ci_pipeline_health.build_pipeline_health(tmp_path)

    assert result["pipeline_health"] == "healthy"
    assert result["checks_passed"] == 12
    assert result["checks_failed"] == 0
    assert result["mvp_ready"] is True
    assert result["release_ready"] is True
    assert result["security_ready"] is True
