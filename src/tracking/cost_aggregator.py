"""Aggregate cost usage across executions and entities."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_float, safe_int, safe_text
from src.tracking.cost_result import build_aggregation_result


class CostAggregator:
    """Aggregate cost usage records."""

    def aggregate_by_execution(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_grouped(records, "execution_id")

    def aggregate_by_campaign(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_grouped(records, "campaign_id")

    def aggregate_by_module(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_grouped(records, "module")

    def aggregate_by_provider(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_grouped(records, "provider")

    def aggregate_by_model(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_grouped(records, "model")

    def aggregate_by_asset(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_grouped(records, "asset_type")

    def summarize_cost(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Return a high-level summary across all records."""

        normalized_records = self._normalize_records(records)
        currencies = list(dict.fromkeys([record["currency"] for record in normalized_records if record["currency"]]))
        currency = currencies[0] if len(currencies) == 1 else (currencies[0] if currencies else "USD")
        warnings: list[str] = []
        if len(currencies) > 1:
            warnings.append("Mixed currencies detected in cost aggregation.")
        summary = {
            "total_cost": round(sum(record["total_cost"] for record in normalized_records), 6),
            "currency": currency,
            "records_count": len(normalized_records),
            "estimated_cost_records": sum(1 for record in normalized_records if record["estimated_cost"]),
            "unknown_pricing_records": sum(1 for record in normalized_records if not record["pricing_found"]),
            "by_provider": self.aggregate_by_provider(records),
            "by_model": self.aggregate_by_model(records),
            "by_module": self.aggregate_by_module(records),
            "by_campaign": self.aggregate_by_campaign(records),
            "by_asset": self.aggregate_by_asset(records),
            "total_input_tokens": sum(record["input_tokens"] for record in normalized_records),
            "total_output_tokens": sum(record["output_tokens"] for record in normalized_records),
            "total_cached_input_tokens": sum(record["cached_input_tokens"] for record in normalized_records),
            "input_cost": round(sum(record["input_cost"] for record in normalized_records), 6),
            "output_cost": round(sum(record["output_cost"] for record in normalized_records), 6),
            "cached_input_cost": round(sum(record["cached_input_cost"] for record in normalized_records), 6),
            "warnings": warnings,
            "errors": [],
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
                    "total_cost": 0.0,
                    "input_cost": 0.0,
                    "output_cost": 0.0,
                    "cached_input_cost": 0.0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "total_cached_input_tokens": 0,
                    "estimated_cost_records": 0,
                    "unknown_pricing_records": 0,
                },
            )
            bucket["records_count"] += 1
            bucket["total_cost"] += record["total_cost"]
            bucket["input_cost"] += record["input_cost"]
            bucket["output_cost"] += record["output_cost"]
            bucket["cached_input_cost"] += record["cached_input_cost"]
            bucket["total_input_tokens"] += record["input_tokens"]
            bucket["total_output_tokens"] += record["output_tokens"]
            bucket["total_cached_input_tokens"] += record["cached_input_tokens"]
            if record["estimated_cost"]:
                bucket["estimated_cost_records"] += 1
            if not record["pricing_found"]:
                bucket["unknown_pricing_records"] += 1
        for bucket in grouped.values():
            bucket["total_cost"] = round(bucket["total_cost"], 6)
            bucket["input_cost"] = round(bucket["input_cost"], 6)
            bucket["output_cost"] = round(bucket["output_cost"], 6)
            bucket["cached_input_cost"] = round(bucket["cached_input_cost"], 6)
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
                    "currency": safe_text(record.get("currency"), limit=32) or "USD",
                    "input_tokens": max(0, safe_int(record.get("input_tokens"), 0)),
                    "output_tokens": max(0, safe_int(record.get("output_tokens"), 0)),
                    "cached_input_tokens": max(0, safe_int(record.get("cached_input_tokens"), 0)),
                    "total_tokens": max(0, safe_int(record.get("total_tokens"), 0)),
                    "input_cost": max(0.0, safe_float(record.get("input_cost"), 0.0)),
                    "output_cost": max(0.0, safe_float(record.get("output_cost"), 0.0)),
                    "cached_input_cost": max(0.0, safe_float(record.get("cached_input_cost"), 0.0)),
                    "total_cost": max(0.0, safe_float(record.get("total_cost"), 0.0)),
                    "estimated_tokens": bool(record.get("estimated_tokens", False)),
                    "estimated_cost": bool(record.get("estimated_cost", False)),
                    "pricing_found": bool(record.get("pricing_found", False)),
                    "pricing_version": safe_text(record.get("pricing_version"), limit=80),
                    "pricing_source": safe_text(record.get("pricing_source"), limit=80),
                    "execution_id": safe_text(record.get("execution_id"), limit=120),
                    "module": safe_text(record.get("module"), limit=120),
                    "operation": safe_text(record.get("operation"), limit=120),
                    "campaign_id": safe_text(record.get("campaign_id"), limit=120),
                    "asset_type": safe_text(record.get("asset_type"), limit=120),
                }
            )
        return normalized
