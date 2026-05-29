from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.reports.markdown_generator import MarkdownReportGenerator


def test_api_markdown_report_generation(auth_services) -> None:
    app = create_app(services={"markdown_report": MarkdownReportGenerator(), **auth_services})
    client = TestClient(app)

    register = client.post(
        "/auth/register",
        json={"email": "reports@example.com", "password": "Password123", "display_name": "Reports User"},
    )
    token = register.json()["data"]["access_token"]

    response = client.post(
        "/reports/markdown",
        json={
            "report_type": "workflow_report",
            "title": "Workflow Report",
            "brand": "wenzel_partner",
            "workflow_result": {
                "workflow_id": "wf-123",
                "workflow_type": "full_campaign_package",
                "status": "completed",
                "summary": {"step_count": 2, "completed_steps": 2, "failed_steps": 0, "skipped_steps": 0},
            },
            "token_summary": {"provider": "openai", "model": "gpt-4o-mini", "total_tokens": 120},
            "cost_summary": {"provider": "openai", "model": "gpt-4o-mini", "currency": "USD", "total_cost": 0.03},
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["report_type"] == "workflow_report"
    assert "## Workflow Overview" in payload["data"]["markdown"]
