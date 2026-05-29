from __future__ import annotations

from src.release.release_score import calculate_release_score


def test_release_score_ready_when_all_sections_pass() -> None:
    result = calculate_release_score(
        {
            "functional_ready": True,
            "technical_ready": True,
            "security_ready": True,
            "deployment_ready": True,
            "observability_ready": True,
            "documentation_ready": True,
            "ci_ready": True,
        }
    )
    assert result["release_status"] == "ready"
    assert result["release_score"] == 100
    assert result["overall_score"] == 100
    assert result["domain_scores"]


def test_release_score_warns_when_sections_missing() -> None:
    result = calculate_release_score({"functional_ready": True, "technical_ready": False})
    assert result["release_status"] in {"warning", "blocked"}
    assert result["release_score"] < 100
