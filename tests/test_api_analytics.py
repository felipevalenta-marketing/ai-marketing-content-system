from __future__ import annotations

from fastapi.testclient import TestClient

from src.analytics.analytics_engine import AnalyticsEngine
from src.api.main import create_app
from src.storage.storage_manager import StorageManager


def _seed_storage(storage: StorageManager) -> None:
    storage.save_record(
        {
            "record_type": "workflow",
            "record_id": "workflow-1",
            "created_at": "2026-05-29T10:00:00+00:00",
            "updated_at": "2026-05-29T10:00:00+00:00",
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "campaign_type": "property_launch",
            "execution_id": "exec-1",
            "source_module": "workflow",
            "payload": {"status": "completed", "summary": {"completed_steps": 3, "skipped_steps": 1, "failed_steps": 0}},
            "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
            "warnings": [],
            "errors": [],
        }
    )
    storage.save_tracking(
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "input_tokens": 12,
            "output_tokens": 8,
            "total_tokens": 20,
            "estimated": False,
            "source": "provider_usage",
            "execution_id": "exec-1",
            "module": "content",
            "operation": "generation",
            "campaign_id": "property_launch",
            "asset_type": "instagram_post",
            "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
            "warnings": [],
            "errors": [],
        },
        "token_usage",
    )


def test_api_analytics_endpoints(tmp_path) -> None:
    storage = StorageManager(storage_root=tmp_path / "data")
    _seed_storage(storage)
    analytics = AnalyticsEngine(storage_manager=storage)
    app = create_app(services={"storage": storage, "analytics": analytics})
    client = TestClient(app)

    health = client.get("/analytics/health")
    summary = client.get("/analytics/summary")
    dashboard = client.get("/analytics/dashboard")
    query = client.post("/analytics/query", json={"analytics_type": "token_analytics", "brand": "wenzel_partner", "platform": "instagram", "filters": {}})

    assert health.status_code == 200
    assert summary.status_code == 200
    assert dashboard.status_code == 200
    assert query.status_code == 200

    health_payload = health.json()
    summary_payload = summary.json()
    dashboard_payload = dashboard.json()
    query_payload = query.json()

    assert health_payload["success"] is True
    assert summary_payload["success"] is True
    assert dashboard_payload["success"] is True
    assert query_payload["success"] is True
    assert "sk-" not in str(health_payload)
    assert "OPENAI_API_KEY" not in str(summary_payload)
    assert summary_payload["data"]["analytics_type"] == "executive_dashboard"
    assert dashboard_payload["data"]["cards"]
    assert query_payload["data"]["analytics_type"] == "token_analytics"

