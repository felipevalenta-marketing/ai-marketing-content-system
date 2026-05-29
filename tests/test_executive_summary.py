from __future__ import annotations

from src.analytics.executive_summary import ExecutiveSummary


def test_executive_summary_handles_empty_data() -> None:
    summary = ExecutiveSummary().build_executive_summary({"sections": {"storage": {"records_count": 0}}})

    assert summary["headline"] == "No persisted activity yet"
    assert summary["next_actions"]


def test_executive_summary_builds_recommendations() -> None:
    summary = ExecutiveSummary().build_executive_summary(
        {
            "sections": {
                "workflows": {"failed_workflows": 1},
                "tokens": {"estimated_records": 1},
                "costs": {"unknown_pricing_records": 1, "total_cost": 0.03, "currency": "USD"},
                "governance": {"warning_count": 2, "approval_rate": 60.0},
                "storage": {"records_count": 5},
            }
        }
    )

    assert summary["approval_status"] == "review"
    assert any("pricing" in item.lower() for item in summary["next_actions"])

