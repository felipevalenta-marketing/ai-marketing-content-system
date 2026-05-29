from __future__ import annotations

from src.analytics.kpi_builder import KPIBuilder


def test_kpi_builder_generates_executive_and_operational_groups() -> None:
    builder = KPIBuilder()
    analytics = {
        "warnings": ["one"],
        "errors": [],
        "sections": {
            "workflows": {"total_workflows": 4, "failed_workflows": 1, "success_rate": 75.0},
            "campaigns": {"records_count": 2, "success_records": 2},
            "generations": {"records_count": 3},
            "assets": {"records_count": 2, "success_records": 2},
            "reports": {"records_count": 1, "success_records": 1},
            "tokens": {"total_tokens": 120, "estimated_records": 1},
            "costs": {"total_cost": 3.25, "currency": "USD", "unknown_pricing_records": 2},
            "governance": {"approval_rate": 80.0},
            "storage": {"records_count": 14},
            "latest_execution_at": "2026-05-29T12:00:00+00:00",
            "latest_report_at": "2026-05-29T13:00:00+00:00",
        },
    }

    kpis = builder.build_kpis(analytics)

    assert kpis["executive"]["total_workflows"]["value"] == 4
    assert kpis["executive"]["total_cost"]["value"] == 3.25
    assert kpis["operational"]["storage_record_count"]["value"] == 14
    assert kpis["operational"]["warning_count"]["value"] == 1
    assert kpis["operational"]["unknown_pricing_records"]["value"] == 2

