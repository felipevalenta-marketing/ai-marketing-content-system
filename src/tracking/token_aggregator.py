"""Aggregate token usage across executions and entities."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import normalize_counts, safe_int, safe_text
from src.tracking.token_result import build_aggregation_result


class TokenAggregator:
    """Aggregate token usage records."""

    def aggregate_by_execution(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate records by execution id."""

        return self._aggregate_grouped(records, "execution_id")

    def aggregate_by_campaign(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate records by campaign id."""

        return self._aggregate_grouped(records, "campaign_id")

    def aggregate_by_module(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate records by module."""

        return self._aggregate_grouped(records, "module")

    def aggregate_by_provider(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate records by provider."""

        return self._aggregate_grouped(records, "provider")

    def aggregate_by_model(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate records by model."""

        return self._aggregate_grouped(records, "model")

    def aggregate_by_asset(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate records by asset type."""

        return self._aggregate_grouped(records, "asset_type")

    def summarize_usage(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a high-level summary across all records."""

        normalized_records = self._normalize_records(records)
        summary = {
            "total_input_tokens": sum(record["input_tokens"] for record in normalized_records),
            "total_output_tokens": sum(record["output_tokens"] for record in normalized_records),
            "total_tokens": sum(record["total_tokens"] for record in normalized_records),
            "estimated_records": sum(1 for record in normalized_records if record["estimated"]),
            "real_usage_records": sum(1 for record in normalized_records if not record["estimated"] and record["source"] == "provider_usage"),
            "records_count": len(normalized_records),
            "by_provider": self.aggregate_by_provider(records),
            "by_model": self.aggregate_by_model(records),
            "by_module": self.aggregate_by_module(records),
            "by_campaign": self.aggregate_by_campaign(records),
            "by_asset": self.aggregate_by_asset(records),
        }
        return summary

    def _aggregate_grouped(self, records: list[dict[str, Any]], group_key: str) -> dict[str, Any]:
        normalized_records = self._normalize_records(records)
        grouped: dict[str, dict[str, Any]] = {}
        for record in normalized_records:
            key = safe_text(record.get(group_key, ""), limit=120) or "unknown"
            bucket = grouped.setdefault(
                key,
                {
                    "records_count": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_tokens": 0,
                    "estimated_records": 0,
                    "real_usage_records": 0,
                },
            )
            bucket["records_count"] += 1
            bucket["total_input_tokens"] += record["input_tokens"]
            bucket["total_output_tokens"] += record["output_tokens"]
            bucket["total_tokens"] += record["total_tokens"]
            if record["estimated"]:
                bucket["estimated_records"] += 1
            elif record["source"] == "provider_usage":
                bucket["real_usage_records"] += 1

        return build_aggregation_result(summary=grouped)

    def _normalize_records(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for record in records or []:
            if not isinstance(record, dict):
                continue
            normalized.append(
                {
                    "provider": safe_text(record.get("provider"), limit=80),
                    "model": safe_text(record.get("model"), limit=80),
                    "input_tokens": max(0, safe_int(record.get("input_tokens"), 0)),
                    "output_tokens": max(0, safe_int(record.get("output_tokens"), 0)),
                    "total_tokens": max(0, safe_int(record.get("total_tokens"), 0)),
                    "estimated": bool(record.get("estimated", False)),
                    "source": safe_text(record.get("source"), limit=80) or "unavailable",
                    "execution_id": safe_text(record.get("execution_id"), limit=120),
                    "module": safe_text(record.get("module"), limit=120),
                    "operation": safe_text(record.get("operation"), limit=120),
                    "campaign_id": safe_text(record.get("campaign_id"), limit=120),
                    "asset_type": safe_text(record.get("asset_type"), limit=120),
                }
            )
        return normalized
