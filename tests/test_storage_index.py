"""Tests for storage index maintenance."""

from __future__ import annotations

from pathlib import Path

from src.storage.storage_index import StorageIndex


def test_storage_index_updates_latest_and_segmented_indexes(tmp_path: Path):
    index = StorageIndex(storage_root=tmp_path)
    record = {
        "record_id": "generation_wenzel_1",
        "record_type": "generation",
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "instagram_post",
        "campaign_type": "property_launch",
        "execution_id": "exec-1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "metadata": {},
    }
    result = index.update(record, str(tmp_path / "generations" / "generation_wenzel_1.json"))
    assert result["success"] is True

    latest = index.read_index("latest")
    assert latest["success"] is True
    assert latest["records"][0]["record_id"] == "generation_wenzel_1"

    by_type = index.read_index("type_generation")
    assert by_type["success"] is True
    assert by_type["records"][0]["brand"] == "wenzel_partner"
