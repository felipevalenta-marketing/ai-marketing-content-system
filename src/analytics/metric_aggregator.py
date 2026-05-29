"""Aggregate analytics records into stable summaries."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.reporting.report_metrics import safe_bool, safe_dict, safe_float, safe_int, safe_list, safe_text


class MetricAggregator:
    def aggregate_counts(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        counts = {"total_records": 0, "success_records": 0, "failed_records": 0, "warning_records": 0, "error_records": 0}
        status_breakdown: dict[str, int] = defaultdict(int)
        for record in safe_list(records):
            if not isinstance(record, dict):
                continue
            counts["total_records"] += 1
            status = self._status(record)
            status_breakdown[status] += 1
            if safe_bool(record.get("success")) or status in {"completed", "approved", "ok", "success"}:
                counts["success_records"] += 1
            if status in {"failed", "error", "rejected"} or safe_bool(record.get("success")) is False:
                counts["failed_records"] += 1
            warnings = safe_list(record.get("warnings"))
            errors = safe_list(record.get("errors"))
            counts["warning_records"] += len(warnings)
            counts["error_records"] += len(errors)
        counts["status_breakdown"] = dict(sorted(status_breakdown.items()))
        counts["success_rate"] = self._percent(counts["success_records"], counts["total_records"])
        counts["failure_rate"] = self._percent(counts["failed_records"], counts["total_records"])
        return counts

    def aggregate_tokens(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        summary = self._aggregate_usage(records, usage_type="tokens")
        return summary

    def aggregate_costs(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        summary = self._aggregate_usage(records, usage_type="costs")
        return summary

    def aggregate_workflows(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        counts = {"total_workflows": 0, "completed_workflows": 0, "failed_workflows": 0, "skipped_workflows": 0, "requires_approval_workflows": 0, "dry_run_workflows": 0, "completed_steps": 0, "skipped_steps": 0, "failed_steps": 0}
        status_breakdown: dict[str, int] = defaultdict(int)
        for record in safe_list(records):
            if not isinstance(record, dict):
                continue
            counts["total_workflows"] += 1
            status = self._status(record)
            status_breakdown[status] += 1
            if status == "completed":
                counts["completed_workflows"] += 1
            if status == "failed":
                counts["failed_workflows"] += 1
            if status == "skipped":
                counts["skipped_workflows"] += 1
            if status == "requires_approval":
                counts["requires_approval_workflows"] += 1
            if status == "dry_run":
                counts["dry_run_workflows"] += 1
            summary = safe_dict(record.get("summary"))
            counts["completed_steps"] += safe_int(summary.get("completed_steps"), 0)
            counts["skipped_steps"] += safe_int(summary.get("skipped_steps"), 0)
            counts["failed_steps"] += safe_int(summary.get("failed_steps"), 0)
        counts["status_breakdown"] = dict(sorted(status_breakdown.items()))
        counts["success_rate"] = self._percent(counts["completed_workflows"], counts["total_workflows"])
        counts["failure_rate"] = self._percent(counts["failed_workflows"], counts["total_workflows"])
        return counts

    def aggregate_governance(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        counts = {"total_records": 0, "approved_records": 0, "warning_count": 0, "error_count": 0, "critical_count": 0, "overall_score_total": 0.0}
        status_breakdown: dict[str, int] = defaultdict(int)
        for record in safe_list(records):
            if not isinstance(record, dict):
                continue
            counts["total_records"] += 1
            status = self._status(record)
            status_breakdown[status] += 1
            if safe_bool(record.get("approved")) or status in {"approved", "ok", "success"}:
                counts["approved_records"] += 1
            warnings = safe_list(record.get("warnings"))
            errors = safe_list(record.get("errors"))
            counts["warning_count"] += len(warnings)
            counts["error_count"] += len(errors)
            counts["critical_count"] += sum(1 for item in errors if "critical" in safe_text(item, limit=120).lower())
            counts["overall_score_total"] += safe_float(record.get("overall_score"), 0.0)
        counts["status_breakdown"] = dict(sorted(status_breakdown.items()))
        counts["approval_rate"] = self._percent(counts["approved_records"], counts["total_records"])
        counts["average_overall_score"] = round(counts["overall_score_total"] / counts["total_records"], 2) if counts["total_records"] else 0.0
        return counts

    def aggregate_by_brand(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_group(records, "brand")

    def aggregate_by_platform(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_group(records, "platform")

    def aggregate_by_content_type(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        return self._aggregate_group(records, "content_type")

    def aggregate_success_rates(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        counts = self.aggregate_counts(records)
        return {"success_rate": counts.get("success_rate", 0.0), "failure_rate": counts.get("failure_rate", 0.0), "records_count": counts.get("total_records", 0)}

    def _aggregate_usage(self, records: list[dict[str, Any]], usage_type: str) -> dict[str, Any]:
        total_input = 0
        total_output = 0
        total_tokens = 0
        total_input_cost = 0.0
        total_output_cost = 0.0
        total_cached_input_cost = 0.0
        total_cost = 0.0
        estimated_records = 0
        real_usage_records = 0
        unknown_pricing_records = 0
        by_provider: dict[str, dict[str, Any]] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "records_count": 0})
        by_model: dict[str, dict[str, Any]] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "records_count": 0})
        by_module: dict[str, dict[str, Any]] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "records_count": 0})
        by_campaign: dict[str, dict[str, Any]] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "records_count": 0})
        by_asset: dict[str, dict[str, Any]] = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "records_count": 0})
        by_provider_cost: dict[str, dict[str, Any]] = defaultdict(lambda: {"input_cost": 0.0, "output_cost": 0.0, "cached_input_cost": 0.0, "total_cost": 0.0, "records_count": 0})
        by_model_cost: dict[str, dict[str, Any]] = defaultdict(lambda: {"input_cost": 0.0, "output_cost": 0.0, "cached_input_cost": 0.0, "total_cost": 0.0, "records_count": 0})
        for record in safe_list(records):
            if not isinstance(record, dict):
                continue
            payload = self._usage_payload(record, usage_type)
            if not payload:
                continue
            input_tokens = safe_int(payload.get("input_tokens"), 0)
            output_tokens = safe_int(payload.get("output_tokens"), 0)
            total = safe_int(payload.get("total_tokens"), input_tokens + output_tokens)
            total_input += input_tokens
            total_output += output_tokens
            total_tokens += total
            if safe_bool(payload.get("estimated")):
                estimated_records += 1
            else:
                real_usage_records += 1
            if usage_type == "costs" and not safe_bool(payload.get("pricing_found", True)):
                unknown_pricing_records += 1
            if usage_type == "costs":
                total_input_cost += safe_float(payload.get("input_cost"), 0.0)
                total_output_cost += safe_float(payload.get("output_cost"), 0.0)
                total_cached_input_cost += safe_float(payload.get("cached_input_cost"), 0.0)
                total_cost += safe_float(payload.get("total_cost"), 0.0)
            provider = self._provider(record, payload)
            model = self._model(record, payload)
            module = self._module(record, payload)
            campaign = self._campaign(record, payload)
            asset = self._asset(record, payload)
            bucket = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total,
            }
            self._rollup(by_provider, provider, bucket)
            self._rollup(by_model, model, bucket)
            self._rollup(by_module, module, bucket)
            self._rollup(by_campaign, campaign, bucket)
            self._rollup(by_asset, asset, bucket)
            if usage_type == "costs":
                self._rollup_cost(by_provider_cost, provider, payload)
                self._rollup_cost(by_model_cost, model, payload)
        summary = {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_tokens,
            "estimated_records": estimated_records,
            "real_usage_records": real_usage_records,
            "records_count": len(safe_list(records)),
            "by_provider": dict(by_provider),
            "by_model": dict(by_model),
            "by_module": dict(by_module),
            "by_campaign": dict(by_campaign),
            "by_asset": dict(by_asset),
        }
        if usage_type == "costs":
            summary["estimated_cost_records"] = estimated_records
            summary["unknown_pricing_records"] = unknown_pricing_records
            summary["input_cost"] = round(total_input_cost, 6)
            summary["output_cost"] = round(total_output_cost, 6)
            summary["cached_input_cost"] = round(total_cached_input_cost, 6)
            summary["total_cost"] = round(total_cost, 6)
            summary["currency"] = self._currency(records)
            summary["by_provider_cost"] = dict(by_provider_cost)
            summary["by_model_cost"] = dict(by_model_cost)
        return summary

    def _aggregate_group(self, records: list[dict[str, Any]], key: str) -> dict[str, Any]:
        groups: dict[str, int] = defaultdict(int)
        for record in safe_list(records):
            if not isinstance(record, dict):
                continue
            fallback_key = "brand_id" if key == "brand" else key
            groups[safe_text(record.get(key) or record.get(fallback_key) or safe_dict(record.get("metadata")).get(key) or safe_dict(record.get("metadata")).get(fallback_key) or "unknown", limit=80).lower() or "unknown"] += 1
        return {"groups": dict(sorted(groups.items())), "records_count": len(safe_list(records))}

    def _usage_payload(self, record: dict[str, Any], usage_type: str) -> dict[str, Any]:
        candidates = []
        if usage_type == "tokens":
            candidates = ["token_usage", "execution_token_summary", "module_token_summary", "provider_token_summary", "workflow_token_summary", "summary", "payload"]
        else:
            candidates = ["cost_usage", "execution_cost_summary", "module_cost_summary", "provider_cost_summary", "model_cost_summary", "summary", "payload"]
        for key in candidates:
            value = safe_dict(record.get(key))
            if value:
                return value
        return {}

    def _provider(self, record: dict[str, Any], payload: dict[str, Any]) -> str:
        return safe_text(record.get("provider") or payload.get("provider") or safe_dict(record.get("metadata")).get("provider") or "unknown", limit=80).lower() or "unknown"

    def _model(self, record: dict[str, Any], payload: dict[str, Any]) -> str:
        return safe_text(record.get("model") or payload.get("model") or safe_dict(record.get("metadata")).get("model") or "unknown", limit=80).lower() or "unknown"

    def _module(self, record: dict[str, Any], payload: dict[str, Any]) -> str:
        return safe_text(record.get("module") or record.get("source_module") or payload.get("module") or safe_dict(record.get("metadata")).get("module") or "unknown", limit=80).lower() or "unknown"

    def _campaign(self, record: dict[str, Any], payload: dict[str, Any]) -> str:
        return safe_text(record.get("campaign_id") or record.get("campaign_type") or payload.get("campaign_id") or safe_dict(record.get("metadata")).get("campaign_id") or "unknown", limit=80).lower() or "unknown"

    def _asset(self, record: dict[str, Any], payload: dict[str, Any]) -> str:
        return safe_text(record.get("asset_type") or payload.get("asset_type") or safe_dict(record.get("metadata")).get("asset_type") or "unknown", limit=80).lower() or "unknown"

    def _rollup(self, bucket_map: dict[str, dict[str, Any]], key: str, bucket: dict[str, Any]) -> None:
        entry = bucket_map[key]
        entry["input_tokens"] += bucket["input_tokens"]
        entry["output_tokens"] += bucket["output_tokens"]
        entry["total_tokens"] += bucket["total_tokens"]
        entry["records_count"] += 1

    def _rollup_cost(self, bucket_map: dict[str, dict[str, Any]], key: str, payload: dict[str, Any]) -> None:
        entry = bucket_map[key]
        entry["input_cost"] += safe_float(payload.get("input_cost"), 0.0)
        entry["output_cost"] += safe_float(payload.get("output_cost"), 0.0)
        entry["cached_input_cost"] += safe_float(payload.get("cached_input_cost"), 0.0)
        entry["total_cost"] += safe_float(payload.get("total_cost"), 0.0)
        entry["records_count"] += 1

    def _status(self, record: dict[str, Any]) -> str:
        return safe_text(record.get("status") or record.get("workflow_status") or safe_dict(record.get("payload")).get("status") or "unknown", limit=80).lower() or "unknown"

    def _currency(self, records: list[dict[str, Any]]) -> str:
        for record in safe_list(records):
            if not isinstance(record, dict):
                continue
            payload = self._usage_payload(record, "costs")
            currency = safe_text(payload.get("currency") or record.get("currency") or "USD", limit=16)
            if currency:
                return currency
        return "USD"

    def _percent(self, part: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round((part / total) * 100.0, 2)
