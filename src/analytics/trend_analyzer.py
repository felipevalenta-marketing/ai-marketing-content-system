"""Trend helpers for simple analytics grouping."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from src.reporting.report_metrics import safe_dict, safe_list, safe_text


class TrendAnalyzer:
    def group_by_day(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        groups: dict[str, int] = defaultdict(int)
        for record in safe_list(records):
            if not isinstance(record, dict):
                continue
            day = self._date_key(record)
            groups[day] += 1
        return {"groups": dict(sorted(groups.items())), "total_records": len(safe_list(records))}

    def group_by_brand(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._group(records, "brand")

    def group_by_platform(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._group(records, "platform")

    def summarize_recent_activity(self, records: list[dict[str, Any]], limit: int = 10) -> list[dict[str, Any]]:
        ordered = sorted(
            [record for record in safe_list(records) if isinstance(record, dict)],
            key=lambda item: self._timestamp_sort_key(item),
            reverse=True,
        )
        recent: list[dict[str, Any]] = []
        for record in ordered[: max(0, limit)]:
            recent.append(
                {
                    "record_id": safe_text(record.get("record_id"), limit=120),
                    "record_type": safe_text(record.get("record_type"), limit=80),
                    "brand": safe_text(record.get("brand"), limit=80),
                    "platform": safe_text(record.get("platform"), limit=80),
                    "content_type": safe_text(record.get("content_type"), limit=80),
                    "campaign_type": safe_text(record.get("campaign_type"), limit=80),
                    "status": self._status(record),
                    "created_at": safe_text(record.get("created_at"), limit=80),
                    "source_module": safe_text(record.get("source_module"), limit=80),
                }
            )
        return recent

    def _group(self, records: list[dict[str, Any]], key: str) -> dict[str, Any]:
        groups: dict[str, int] = defaultdict(int)
        for record in safe_list(records):
            if not isinstance(record, dict):
                continue
            value = safe_text(record.get(key) or safe_dict(record.get("metadata")).get(key) or "unknown", limit=80).lower() or "unknown"
            groups[value] += 1
        return {"groups": dict(sorted(groups.items())), "total_records": len(safe_list(records))}

    def _date_key(self, record: dict[str, Any]) -> str:
        timestamp = safe_text(record.get("created_at") or record.get("updated_at") or "", limit=80)
        if not timestamp:
            return "unknown"
        return timestamp[:10]

    def _timestamp_sort_key(self, record: dict[str, Any]) -> str:
        timestamp = safe_text(record.get("created_at") or record.get("updated_at") or "", limit=80)
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).isoformat()
        except Exception:
            return timestamp

    def _status(self, record: dict[str, Any]) -> str:
        return safe_text(record.get("status") or record.get("workflow_status") or safe_dict(record.get("payload")).get("status") or "unknown", limit=80).lower() or "unknown"
