"""Build executive and operational KPIs."""

from __future__ import annotations

from typing import Any

from src.analytics.analytics_contracts import KPIContract
from src.reporting.report_metrics import safe_dict, safe_float, safe_int, safe_list, safe_text


class KPIBuilder:
    def build_kpis(self, analytics: dict[str, Any]) -> dict[str, Any]:
        sections = safe_dict(analytics.get("sections"))
        workflows = safe_dict(sections.get("workflows"))
        campaigns = safe_dict(sections.get("campaigns"))
        generations = safe_dict(sections.get("generations"))
        assets = safe_dict(sections.get("assets"))
        reports = safe_dict(sections.get("reports"))
        tokens = safe_dict(sections.get("tokens"))
        costs = safe_dict(sections.get("costs"))
        governance = safe_dict(sections.get("governance"))
        storage = safe_dict(sections.get("storage"))

        total_workflows = safe_int(workflows.get("total_workflows"), 0)
        total_generations = safe_int(generations.get("records_count"), safe_int(campaigns.get("records_count"), 0))
        total_campaigns = safe_int(campaigns.get("records_count"), 0)
        total_assets = safe_int(assets.get("records_count"), 0)
        total_reports = safe_int(reports.get("records_count"), 0)
        total_tokens = safe_int(tokens.get("total_tokens"), 0)
        total_cost = safe_float(costs.get("total_cost"), 0.0)
        avg_cost_per_generation = round(total_cost / total_generations, 6) if total_generations else 0.0
        avg_tokens_per_generation = round(total_tokens / total_generations, 2) if total_generations else 0.0
        governance_rate = safe_float(governance.get("approval_rate"), 0.0)
        workflow_success_rate = safe_float(workflows.get("success_rate"), 0.0)
        content_success_rate = self._content_success_rate(campaigns, assets, reports)

        executive = {
            "total_workflows": self._kpi("Total Workflows", total_workflows, "", self._status(total_workflows), "Number of workflow executions in the selected period."),
            "total_generations": self._kpi("Total Generations", total_generations, "", self._status(total_generations), "Number of generated content records."),
            "total_campaigns": self._kpi("Total Campaigns", total_campaigns, "", self._status(total_campaigns), "Campaign records available for analysis."),
            "total_assets": self._kpi("Total Assets", total_assets, "", self._status(total_assets), "Asset records available for analysis."),
            "total_reports": self._kpi("Total Reports", total_reports, "", self._status(total_reports), "Persisted report records available."),
            "total_tokens": self._kpi("Total Tokens", total_tokens, "", self._status(total_tokens), "Total token usage across tracked records."),
            "total_cost": self._kpi("Total Cost", total_cost, self._currency(costs), self._status(total_cost), "Estimated or known AI usage cost."),
            "average_cost_per_generation": self._kpi("Average Cost / Generation", avg_cost_per_generation, self._currency(costs), self._status(avg_cost_per_generation), "Average cost for each generation record."),
            "average_tokens_per_generation": self._kpi("Average Tokens / Generation", avg_tokens_per_generation, "", self._status(avg_tokens_per_generation), "Average token usage for each generation record."),
            "governance_approval_rate": self._kpi("Governance Approval Rate", governance_rate, "%", self._rate_status(governance_rate), "Approval rate from governance summaries."),
            "workflow_success_rate": self._kpi("Workflow Success Rate", workflow_success_rate, "%", self._rate_status(workflow_success_rate), "Success rate of recorded workflows."),
            "content_success_rate": self._kpi("Content Success Rate", content_success_rate, "%", self._rate_status(content_success_rate), "Success rate of content and asset outputs."),
        }

        operational = {
            "storage_record_count": self._kpi("Storage Records", safe_int(storage.get("records_count"), 0), "", self._status(safe_int(storage.get("records_count"), 0)), "Total records available in storage."),
            "latest_execution_at": self._kpi("Latest Execution", safe_text(sections.get("latest_execution_at") or "", limit=80), "", "neutral", "Most recent execution timestamp."),
            "latest_report_at": self._kpi("Latest Report", safe_text(sections.get("latest_report_at") or "", limit=80), "", "neutral", "Most recent report timestamp."),
            "failed_workflows": self._kpi("Failed Workflows", safe_int(workflows.get("failed_workflows"), 0), "", self._error_status(safe_int(workflows.get("failed_workflows"), 0)), "Number of failed workflows."),
            "warning_count": self._kpi("Warnings", safe_int(analytics.get("warnings_count", len(safe_list(analytics.get("warnings")))), 0), "", self._warning_status(safe_int(analytics.get("warnings_count", len(safe_list(analytics.get("warnings")))), 0)), "Warning count across analytics inputs."),
            "error_count": self._kpi("Errors", safe_int(analytics.get("errors_count", len(safe_list(analytics.get("errors")))), 0), "", self._error_status(safe_int(analytics.get("errors_count", len(safe_list(analytics.get("errors")))), 0)), "Error count across analytics inputs."),
            "estimated_usage_records": self._kpi("Estimated Usage Records", safe_int(tokens.get("estimated_records"), 0), "", self._warning_status(safe_int(tokens.get("estimated_records"), 0)), "Token records estimated instead of provider-reported."),
            "unknown_pricing_records": self._kpi("Unknown Pricing Records", safe_int(costs.get("unknown_pricing_records"), 0), "", self._warning_status(safe_int(costs.get("unknown_pricing_records"), 0)), "Cost records without known pricing."),
        }

        return {"executive": executive, "operational": operational}

    def _kpi(self, label: str, value: Any, unit: str, status: str, description: str) -> dict[str, Any]:
        return KPIContract(label=label, value=value, unit=unit, status=status, description=description, metadata={}).to_dict()

    def _currency(self, costs: dict[str, Any]) -> str:
        return safe_text(costs.get("currency") or "USD", limit=16)

    def _status(self, value: float | int) -> str:
        return "success" if value else "neutral"

    def _warning_status(self, value: int) -> str:
        return "warning" if value > 0 else "success"

    def _error_status(self, value: int) -> str:
        return "error" if value > 0 else "success"

    def _rate_status(self, value: float) -> str:
        if value >= 90:
            return "success"
        if value >= 70:
            return "warning"
        return "error"

    def _content_success_rate(self, campaigns: dict[str, Any], assets: dict[str, Any], reports: dict[str, Any]) -> float:
        total = safe_int(campaigns.get("records_count"), 0) + safe_int(assets.get("records_count"), 0) + safe_int(reports.get("records_count"), 0)
        if total <= 0:
            return 0.0
        success = sum(
            1
            for section in (campaigns, assets, reports)
            if safe_int(section.get("success_records"), safe_int(section.get("total_records"), safe_int(section.get("records_count"), 0))) > 0
        )
        return round((success / 3) * 100.0, 2)
