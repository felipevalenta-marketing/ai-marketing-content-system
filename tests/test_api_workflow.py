from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app


class FakeWorkflowEngine:
    def create_workflow(self, request: dict[str, object]) -> dict[str, object]:
        return {
            "success": True,
            "workflow_id": "wf-123",
            "workflow_type": request.get("workflow_type", ""),
            "status": "dry_run",
            "started_at": "2026-05-29T00:00:00+00:00",
            "completed_at": "2026-05-29T00:00:01+00:00",
            "duration_seconds": 1.0,
            "workflow_state": {"history": [{"state": "planned"}], "step_outputs": {}},
            "markdown_report": {"markdown": "# Workflow Report"},
            "token_summary": {"provider": "openai", "model": "gpt-4o-mini", "total_tokens": 12},
            "cost_summary": {"provider": "openai", "model": "gpt-4o-mini", "currency": "USD", "total_cost": 0.01},
            "storage_summary": {"storage_root": "data", "records_saved": 0},
            "warnings": [],
            "errors": [],
        }


def test_api_workflow_returns_structured_result(auth_services) -> None:
    app = create_app(services={"workflow": FakeWorkflowEngine(), "users": auth_services["users"], "auth": auth_services["auth"]})
    client = TestClient(app)

    register = client.post(
        "/auth/register",
        json={"email": "workflow@example.com", "password": "Password123", "display_name": "Workflow User"},
    )
    token = register.json()["data"]["access_token"]

    response = client.post(
        "/workflow",
        json={
            "workflow_type": "full_campaign_package",
            "brand": "wenzel_partner",
            "platform": "instagram",
            "platforms": ["instagram", "facebook"],
            "content_type": "instagram_post",
            "campaign_type": "property_launch",
            "objective": "generate_leads",
            "audience": "relocation_clients",
            "location": "sant_llorenc_des_cardassar",
            "assets": ["image_prompt", "video_prompt"],
            "dry_run": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["workflow_id"] == "wf-123"
    assert payload["data"]["markdown_report"]["markdown"] == "# Workflow Report"
