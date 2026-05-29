"""Build frontend-ready dashboard payloads from analytics summaries."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_dict, safe_float, safe_int, safe_list, safe_text


class DashboardPayloadBuilder:
    def build_dashboard_payload(self, analytics: dict[str, Any]) -> dict[str, Any]:
        kpis = safe_dict(analytics.get("kpis"))
        executive = safe_dict(kpis.get("executive"))
        operational = safe_dict(kpis.get("operational"))
        sections = safe_dict(analytics.get("sections"))
        health = self._build_health(analytics)
        cards = self._build_cards(executive, operational)
        tables = {
            "workflow_status": self._build_status_table(sections.get("workflows")),
            "token_usage": self._build_usage_table(sections.get("tokens"), usage_type="tokens"),
            "cost_usage": self._build_usage_table(sections.get("costs"), usage_type="costs"),
            "governance": self._build_governance_table(sections.get("governance")),
            "storage": self._build_storage_table(sections.get("storage")),
        }
        summaries = {
            "executive": safe_dict(analytics.get("executive_summary")),
            "kpis": kpis,
            "trends": safe_dict(analytics.get("trends")),
            "insights": safe_list(analytics.get("insights")),
            "recommendations": safe_list(analytics.get("recommendations")),
        }
        recent_activity = safe_list(safe_dict(analytics.get("trends")).get("recent_activity"))
        return {
            "cards": cards,
            "tables": tables,
            "summaries": summaries,
            "recent_activity": recent_activity,
            "health": health,
            "warnings": [safe_text(item, limit=240) for item in safe_list(analytics.get("warnings")) if safe_text(item, limit=240)],
            "errors": [safe_text(item, limit=240) for item in safe_list(analytics.get("errors")) if safe_text(item, limit=240)],
        }

    def _build_cards(self, executive: dict[str, Any], operational: dict[str, Any]) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for key in ("total_workflows", "total_generations", "total_tokens", "total_cost", "governance_approval_rate", "workflow_success_rate"):
            item = safe_dict(executive.get(key))
            if item:
                cards.append(self._card_from_kpi(item))
        for key in ("storage_record_count", "failed_workflows", "warning_count", "error_count", "estimated_usage_records", "unknown_pricing_records"):
            item = safe_dict(operational.get(key))
            if item:
                cards.append(self._card_from_kpi(item))
        return cards

    def _card_from_kpi(self, kpi: dict[str, Any]) -> dict[str, Any]:
        return {
            "label": safe_text(kpi.get("label"), limit=80),
            "value": safe_text(kpi.get("value"), limit=120),
            "unit": safe_text(kpi.get("unit"), limit=16),
            "status": safe_text(kpi.get("status"), limit=16),
            "description": safe_text(kpi.get("description"), limit=240),
        }

    def _build_status_table(self, workflows: dict[str, Any] | None) -> list[dict[str, Any]]:
        summary = safe_dict(workflows)
        return [
            {"label": "Total", "value": safe_int(summary.get("total_workflows"), 0)},
            {"label": "Completed", "value": safe_int(summary.get("completed_workflows"), 0)},
            {"label": "Failed", "value": safe_int(summary.get("failed_workflows"), 0)},
            {"label": "Skipped", "value": safe_int(summary.get("skipped_workflows"), 0)},
            {"label": "Requires Approval", "value": safe_int(summary.get("requires_approval_workflows"), 0)},
        ]

    def _build_usage_table(self, summary: dict[str, Any] | None, usage_type: str) -> list[dict[str, Any]]:
        payload = safe_dict(summary)
        rows: list[dict[str, Any]] = []
        breakdown = safe_dict(payload.get("by_provider_cost" if usage_type == "costs" else "by_provider"))
        for key, value in list(breakdown.items())[:6]:
            value_dict = safe_dict(value)
            rows.append(
                {
                    "label": safe_text(key, limit=80),
                    "input": safe_int(value_dict.get("input_tokens"), 0) if usage_type == "tokens" else safe_float(value_dict.get("input_cost"), 0.0),
                    "output": safe_int(value_dict.get("output_tokens"), 0) if usage_type == "tokens" else safe_float(value_dict.get("output_cost"), 0.0),
                    "total": safe_int(value_dict.get("total_tokens"), 0) if usage_type == "tokens" else safe_float(value_dict.get("total_cost"), 0.0),
                }
            )
        return rows

    def _build_governance_table(self, summary: dict[str, Any] | None) -> list[dict[str, Any]]:
        payload = safe_dict(summary)
        return [
            {"label": "Approval Rate", "value": safe_float(payload.get("approval_rate"), 0.0)},
            {"label": "Warnings", "value": safe_int(payload.get("warning_count"), 0)},
            {"label": "Errors", "value": safe_int(payload.get("error_count"), 0)},
            {"label": "Average Score", "value": safe_float(payload.get("average_overall_score"), 0.0)},
        ]

    def _build_storage_table(self, summary: dict[str, Any] | None) -> list[dict[str, Any]]:
        payload = safe_dict(summary)
        return [
            {"label": "Records", "value": safe_int(payload.get("records_count"), 0)},
            {"label": "Latest Execution", "value": safe_text(payload.get("latest_execution_at"), limit=80)},
            {"label": "Latest Report", "value": safe_text(payload.get("latest_report_at"), limit=80)},
        ]

    def _build_health(self, analytics: dict[str, Any]) -> dict[str, Any]:
        sections = safe_dict(analytics.get("sections"))
        storage = safe_dict(sections.get("storage"))
        workflows = safe_dict(sections.get("workflows"))
        tokens = safe_dict(sections.get("tokens"))
        costs = safe_dict(sections.get("costs"))
        if safe_int(storage.get("records_count"), 0) <= 0:
            status = "empty"
        elif safe_int(workflows.get("failed_workflows"), 0) > 0:
            status = "warning"
        elif safe_int(tokens.get("estimated_records"), 0) > 0 or safe_int(costs.get("unknown_pricing_records"), 0) > 0:
            status = "warning"
        else:
            status = "healthy"
        return {
            "status": status,
            "records_count": safe_int(storage.get("records_count"), 0),
            "workflow_count": safe_int(workflows.get("total_workflows"), 0),
            "warnings": len(safe_list(analytics.get("warnings"))),
            "errors": len(safe_list(analytics.get("errors"))),
        }
