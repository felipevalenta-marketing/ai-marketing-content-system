"""Collect storage-backed metrics for analytics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.reporting.report_metrics import safe_dict, safe_list, safe_text


class MetricCollector:
    def __init__(self, storage_manager: Any | None = None, logger: Any | None = None) -> None:
        self.storage_manager = storage_manager
        self.logger = logger
        self.warnings: list[str] = []

    def clear_warnings(self) -> None:
        self.warnings = []

    def collect_records(self, record_type: str | None = None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self.storage_manager is None:
            self.warnings.append("StorageManager is unavailable.")
            return []
        try:
            records = self.storage_manager.list_records(record_type=record_type)
        except Exception as exc:
            self.warnings.append(f"Unable to collect records: {exc}")
            return []
        filtered = [record for record in records if isinstance(record, dict) and self._matches(record, filters or {})]
        if record_type and not filtered:
            self.warnings.append(f"No records found for {record_type}.")
        if not record_type and not filtered:
            self.warnings.append("No records found in storage.")
        return filtered

    def collect_workflow_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.collect_records("workflow", filters)

    def collect_generation_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.collect_records("generation", filters)

    def collect_campaign_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.collect_records("campaign", filters)

    def collect_asset_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.collect_records("asset", filters)

    def collect_report_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.collect_records("report", filters)

    def collect_token_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.collect_records("token_usage", filters)

    def collect_cost_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.collect_records("cost_usage", filters)

    def collect_governance_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.collect_records("report", filters) + self.collect_records("workflow", filters)

    def _matches(self, record: dict[str, Any], filters: dict[str, Any]) -> bool:
        if not filters:
            return True
        metadata = safe_dict(record.get("metadata"))
        payload = safe_dict(record.get("payload"))
        brand_fallback = record.get("brand_id") or metadata.get("brand_id") or record.get("brand") or metadata.get("brand")
        for key, expected in filters.items():
            if expected in (None, ""):
                continue
            actual = record.get(key, metadata.get(key, payload.get(key)))
            if key == "brand" and actual in (None, ""):
                actual = brand_fallback
            if key == "date_range":
                if not self._matches_date_range(record, safe_dict(expected)):
                    return False
                continue
            if isinstance(expected, list):
                expected_set = {safe_text(item, limit=120).strip().lower() for item in expected if safe_text(item, limit=120)}
                actual_text = safe_text(actual, limit=120).strip().lower()
                if actual_text not in expected_set:
                    return False
                continue
            if safe_text(actual, limit=120).strip().lower() != safe_text(expected, limit=120).strip().lower():
                return False
        return True

    def _matches_date_range(self, record: dict[str, Any], date_range: dict[str, Any]) -> bool:
        start = safe_text(date_range.get("start"), limit=40)
        end = safe_text(date_range.get("end"), limit=40)
        timestamp = safe_text(record.get("created_at") or record.get("updated_at") or "", limit=80)
        if not timestamp:
            return True
        try:
            record_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except Exception:
            return True
        if start:
            try:
                if record_dt < datetime.fromisoformat(start.replace("Z", "+00:00")):
                    return False
            except Exception:
                pass
        if end:
            try:
                if record_dt > datetime.fromisoformat(end.replace("Z", "+00:00")):
                    return False
            except Exception:
                pass
        return True
