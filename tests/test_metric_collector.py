from __future__ import annotations

from src.analytics.metric_collector import MetricCollector
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
            "payload": {"status": "completed", "summary": {"completed_steps": 3, "failed_steps": 0, "skipped_steps": 0}},
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


def test_metric_collector_empty_storage_warns(tmp_path) -> None:
    storage = StorageManager(storage_root=tmp_path / "data")
    collector = MetricCollector(storage_manager=storage)

    records = collector.collect_workflow_records()

    assert records == []
    assert any("No records found" in warning for warning in collector.warnings)


def test_metric_collector_filters_records(tmp_path) -> None:
    storage = StorageManager(storage_root=tmp_path / "data")
    _seed_storage(storage)
    collector = MetricCollector(storage_manager=storage)

    records = collector.collect_workflow_records({"brand": "wenzel_partner"})

    assert len(records) == 1
    assert records[0]["brand"] == "wenzel_partner"

