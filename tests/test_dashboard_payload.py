from __future__ import annotations

from src.analytics.dashboard_payload import DashboardPayloadBuilder


def test_dashboard_payload_structure() -> None:
    builder = DashboardPayloadBuilder()
    analytics = {
        "analytics_type": "executive_dashboard",
        "warnings": ["safe warning"],
        "errors": [],
        "executive_summary": {"headline": "Ready", "outcome": "Stable"},
        "kpis": {
            "executive": {
                "total_workflows": {"label": "Total Workflows", "value": 3, "unit": "", "status": "success", "description": ""},
                "total_tokens": {"label": "Total Tokens", "value": 100, "unit": "", "status": "success", "description": ""},
            },
            "operational": {},
        },
        "sections": {
            "workflows": {"total_workflows": 3, "completed_workflows": 2, "failed_workflows": 1},
            "tokens": {"total_tokens": 100, "estimated_records": 1},
            "costs": {"total_cost": 1.5, "currency": "USD", "unknown_pricing_records": 1},
            "governance": {"approval_rate": 80.0, "warning_count": 1, "error_count": 0},
            "storage": {"records_count": 4, "latest_execution_at": "2026-05-29T12:00:00+00:00", "latest_report_at": "2026-05-29T13:00:00+00:00"},
            "brand_breakdown": {"groups": {"wenzel_partner": 3}},
            "platform_breakdown": {"groups": {"instagram": 3}},
            "content_type_breakdown": {"groups": {"report": 1}},
        },
        "trends": {"recent_activity": [{"record_id": "1"}]},
        "insights": ["One insight"],
        "recommendations": ["One recommendation"],
    }

    payload = builder.build_dashboard_payload(analytics)

    assert payload["cards"]
    assert payload["tables"]["workflow_status"]
    assert payload["health"]["status"] in {"healthy", "warning", "empty"}
    assert payload["recent_activity"]

