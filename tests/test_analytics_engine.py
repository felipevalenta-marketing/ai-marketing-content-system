from __future__ import annotations

from src.analytics.analytics_engine import AnalyticsEngine
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
            "payload": {
                "status": "completed",
                "summary": {"completed_steps": 3, "skipped_steps": 1, "failed_steps": 0},
                "workflow_snapshot": {"status": "completed"},
                "workflow_state_history": [{"status": "planned"}, {"status": "running"}, {"status": "completed"}],
                "workflow_timeline": [{"status": "planned"}, {"status": "completed"}],
                "workflow_status_transitions": [{"from": "running", "to": "completed"}],
            },
            "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
            "warnings": [],
            "errors": [],
        }
    )
    storage.save_record(
        {
            "record_type": "generation",
            "record_id": "generation-1",
            "created_at": "2026-05-29T11:00:00+00:00",
            "updated_at": "2026-05-29T11:00:00+00:00",
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "campaign_type": "property_launch",
            "execution_id": "exec-1",
            "source_module": "pipeline",
            "payload": {"success": True, "status": "completed"},
            "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
            "warnings": [],
            "errors": [],
        }
    )
    storage.save_record(
        {
            "record_type": "campaign",
            "record_id": "campaign-1",
            "created_at": "2026-05-29T11:30:00+00:00",
            "updated_at": "2026-05-29T11:30:00+00:00",
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "campaign_type": "property_launch",
            "execution_id": "exec-1",
            "source_module": "campaigns",
            "payload": {"success": True, "status": "completed"},
            "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
            "warnings": [],
            "errors": [],
        }
    )
    storage.save_record(
        {
            "record_type": "asset",
            "record_id": "asset-1",
            "created_at": "2026-05-29T11:45:00+00:00",
            "updated_at": "2026-05-29T11:45:00+00:00",
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "campaign_type": "property_launch",
            "execution_id": "exec-1",
            "source_module": "assets",
            "payload": {"success": True, "status": "ready"},
            "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
            "warnings": [],
            "errors": [],
        }
    )
    storage.save_record(
        {
            "record_type": "report",
            "record_id": "report-1",
            "created_at": "2026-05-29T12:00:00+00:00",
            "updated_at": "2026-05-29T12:00:00+00:00",
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "campaign_type": "property_launch",
            "execution_id": "exec-1",
            "source_module": "reporting",
            "consolidated_report": {"title": "Latest Report", "summary": {"status": "success"}, "warnings": [], "errors": []},
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
    storage.save_tracking(
        {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "currency": "USD",
            "input_tokens": 12,
            "output_tokens": 8,
            "cached_input_tokens": 0,
            "total_tokens": 20,
            "input_cost": 0.01,
            "output_cost": 0.02,
            "cached_input_cost": 0.0,
            "total_cost": 0.03,
            "estimated_tokens": False,
            "estimated_cost": False,
            "pricing_found": True,
            "pricing_version": "local_default",
            "pricing_source": "configurable",
            "execution_id": "exec-1",
            "module": "content",
            "operation": "generation",
            "campaign_id": "property_launch",
            "asset_type": "instagram_post",
            "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
            "warnings": [],
            "errors": [],
        },
        "cost_usage",
    )


def test_analytics_engine_empty_storage(tmp_path) -> None:
    storage = StorageManager(storage_root=tmp_path / "data")
    engine = AnalyticsEngine(storage_manager=storage)

    result = engine.generate_executive_dashboard({"analytics_type": "executive_dashboard"})

    assert result["success"] is True
    assert result["kpis"]["executive"]["total_workflows"]["value"] == 0
    assert any("No persisted records" in item for item in result["insights"])
    assert "Run a workflow with persistence enabled." in result["recommendations"]
    assert "Generate content with report enabled." in result["recommendations"]
    assert "Check storage records." in result["recommendations"]
    assert "Review token/cost tracking." in result["recommendations"]


def test_analytics_engine_populated_storage(tmp_path) -> None:
    storage = StorageManager(storage_root=tmp_path / "data")
    _seed_storage(storage)
    engine = AnalyticsEngine(storage_manager=storage)

    result = engine.generate_executive_dashboard(
        {
            "analytics_type": "executive_dashboard",
            "brand": "wenzel_partner",
            "platform": "instagram",
            "date_range": {"start": "", "end": ""},
            "filters": {},
            "include_storage": True,
            "include_tokens": True,
            "include_costs": True,
            "include_governance": True,
            "include_reports": True,
        }
    )

    assert result["success"] is True
    assert result["kpis"]["executive"]["total_workflows"]["value"] == 1
    assert result["dashboard_payload"]["cards"]
    assert result["sections"]["tokens"]["total_tokens"] == 20
    assert result["sections"]["costs"]["total_cost"] == 0.03
    assert result["sections"]["workflow_snapshot"]["status"] == "completed"
    assert result["sections"]["workflow_state_history"]
    assert result["sections"]["workflow_timeline"]
    assert result["sections"]["workflow_status_transitions"]
