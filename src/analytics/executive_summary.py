"""Build concise executive summaries for analytics dashboards."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_dict, safe_float, safe_int, safe_list, safe_text


class ExecutiveSummary:
    def build_executive_summary(self, analytics: dict[str, Any]) -> dict[str, Any]:
        sections = safe_dict(analytics.get("sections"))
        workflows = safe_dict(sections.get("workflows"))
        tokens = safe_dict(sections.get("tokens"))
        costs = safe_dict(sections.get("costs"))
        governance = safe_dict(sections.get("governance"))
        storage = safe_dict(sections.get("storage"))
        latest_status = safe_text(analytics.get("analytics_type") or "executive_dashboard", limit=80)
        headline = self._headline(workflows, storage)
        return {
            "headline": headline,
            "outcome": self._outcome(workflows, storage),
            "approval_status": self._approval_status(governance),
            "generated_assets": safe_int(sections.get("assets", {}).get("records_count"), 0),
            "workflow_status": safe_text(workflows.get("status_breakdown", {}), limit=240),
            "token_summary": self.build_activity_summary(analytics),
            "cost_summary": self.build_cost_summary(analytics),
            "governance_summary": self.build_governance_summary(analytics),
            "key_warnings": self._warnings(analytics),
            "critical_errors": self._errors(analytics),
            "next_actions": self.build_recommendations(analytics),
            "report_type": latest_status,
            "activity_status": "no_data" if safe_int(storage.get("records_count"), 0) <= 0 else "active",
        }

    def build_activity_summary(self, analytics: dict[str, Any]) -> str:
        sections = safe_dict(analytics.get("sections"))
        workflows = safe_dict(sections.get("workflows"))
        campaigns = safe_dict(sections.get("campaigns"))
        assets = safe_dict(sections.get("assets"))
        reports = safe_dict(sections.get("reports"))
        storage = safe_dict(sections.get("storage"))
        return (
            f"{safe_int(workflows.get('total_workflows'), 0)} workflows, "
            f"{safe_int(campaigns.get('records_count'), 0)} campaigns, "
            f"{safe_int(assets.get('records_count'), 0)} assets, "
            f"{safe_int(reports.get('records_count'), 0)} reports, "
            f"{safe_int(storage.get('records_count'), 0)} stored records."
        )

    def build_cost_summary(self, analytics: dict[str, Any]) -> str:
        sections = safe_dict(analytics.get("sections"))
        costs = safe_dict(sections.get("costs"))
        currency = safe_text(costs.get("currency") or "USD", limit=16)
        return f"Total cost {currency} {safe_float(costs.get('total_cost'), 0.0):.6f} across {safe_int(costs.get('records_count'), 0)} tracked records."

    def build_governance_summary(self, analytics: dict[str, Any]) -> str:
        sections = safe_dict(analytics.get("sections"))
        governance = safe_dict(sections.get("governance"))
        return f"{safe_float(governance.get('approval_rate'), 0.0):.2f}% approval rate with {safe_int(governance.get('warning_count'), 0)} warnings and {safe_int(governance.get('error_count'), 0)} errors."

    def build_recommendations(self, analytics: dict[str, Any]) -> list[str]:
        sections = safe_dict(analytics.get("sections"))
        recommendations: list[str] = []
        if safe_int(safe_dict(sections.get("storage", {})).get("records_count"), 0) <= 0:
            recommendations.extend(
                [
                    "Run a workflow with persistence enabled.",
                    "Generate content with report enabled.",
                    "Check storage records.",
                    "Review token/cost tracking.",
                ]
            )
        if safe_int(safe_dict(sections.get("costs", {})).get("unknown_pricing_records"), 0) > 0:
            recommendations.append("Update pricing records for unknown models to improve cost accuracy.")
        if safe_int(safe_dict(sections.get("governance", {})).get("warning_count"), 0) > 0:
            recommendations.append("Review governance warnings before sharing client-facing outputs.")
        if safe_int(safe_dict(sections.get("workflows", {})).get("failed_workflows"), 0) > 0:
            recommendations.append("Inspect failed workflows and address the earliest failing step.")
        if not recommendations:
            recommendations.append("Continue collecting activity to improve dashboard trend fidelity.")
        return list(dict.fromkeys(recommendations))

    def _headline(self, workflows: dict[str, Any], storage: dict[str, Any]) -> str:
        if safe_int(storage.get("records_count"), 0) <= 0:
            return "No persisted activity yet"
        if safe_int(workflows.get("failed_workflows"), 0) > 0:
            return "Operational attention needed"
        if safe_int(workflows.get("requires_approval_workflows"), 0) > 0:
            return "Workflows awaiting approval"
        return "System operating normally"

    def _outcome(self, workflows: dict[str, Any], storage: dict[str, Any]) -> str:
        if safe_int(storage.get("records_count"), 0) <= 0:
            return "No data collected yet."
        if safe_int(workflows.get("failed_workflows"), 0) > 0:
            return "Recent workflows include failures that need review."
        return "Recent activity is stable."

    def _approval_status(self, governance: dict[str, Any]) -> str:
        return "approved" if safe_float(governance.get("approval_rate"), 0.0) >= 80 else "review"

    def _warnings(self, analytics: dict[str, Any]) -> list[str]:
        return [safe_text(item, limit=240) for item in safe_list(analytics.get("warnings")) if safe_text(item, limit=240)]

    def _errors(self, analytics: dict[str, Any]) -> list[str]:
        return [safe_text(item, limit=240) for item in safe_list(analytics.get("errors")) if safe_text(item, limit=240)]
