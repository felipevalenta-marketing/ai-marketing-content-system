from __future__ import annotations

from src.release.release_checklist import build_release_checklist


def test_release_checklist_counts_all_items_when_ready() -> None:
    result = build_release_checklist(
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
    assert result["total_checks"] == 150
    assert result["passed"] == 150
    assert result["failed"] == 0


def test_release_checklist_marks_pending_when_sections_missing() -> None:
    result = build_release_checklist({"functional_ready": True})
    assert result["passed"] < 150
    assert result["failed"] > 0
