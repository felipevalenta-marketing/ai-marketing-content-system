from __future__ import annotations

from src.release.mvp_certification import build_final_mvp_declaration, build_mvp_certification
from src.release.mvp_maturity import build_mvp_maturity
from src.release.release_governance import build_release_governance
from src.release.release_report_builder import build_executive_summary, build_release_artifact_index


def _ready_summary() -> dict[str, object]:
    return {
        "functional_ready": True,
        "technical_ready": True,
        "security_ready": True,
        "deployment_ready": True,
        "observability_ready": True,
        "ci_ready": True,
        "documentation_ready": True,
        "release_ready": True,
        "release_score": 100,
        "release_status": "ready",
        "version": "1.0.0",
        "functional": {"modules": [{"module": "api", "status": "pass"}]},
        "technical": {},
        "security": {},
        "deployment": {},
        "observability": {},
        "ci": {},
        "documentation": {},
    }


def test_mvp_certification_approves_ready_release() -> None:
    result = build_mvp_certification(summary=_ready_summary())
    assert result["mvp_certified"] is True
    assert result["production_ready"] is True
    assert result["certification_status"] == "approved"


def test_maturity_scoring_production_ready() -> None:
    result = build_mvp_maturity(_ready_summary())
    assert result["maturity_level"] == "production_ready"
    assert result["maturity_score"] >= 95


def test_release_governance_blocks_missing_security() -> None:
    summary = _ready_summary()
    summary["security_ready"] = False
    result = build_release_governance(summary)
    assert result["release_blocked"] is True
    assert result["governance_status"] == "blocked"


def test_executive_summary_and_artifact_index_generate_markdown() -> None:
    summary = _ready_summary()
    summary["certification"] = build_mvp_certification(summary=summary)
    summary["maturity"] = build_mvp_maturity(summary)
    executive = build_executive_summary(summary)
    artifacts = build_release_artifact_index()
    declaration = build_final_mvp_declaration(summary=summary)
    assert "MVP Executive Summary" in executive
    assert "Release Artifacts" in artifacts
    assert declaration["mvp_complete"] is True
