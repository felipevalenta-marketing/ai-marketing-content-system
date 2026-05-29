"""Deterministic analytics insights and recommendations."""

from __future__ import annotations

from collections import Counter
from typing import Any

from src.reporting.report_metrics import safe_dict, safe_int, safe_list, safe_text


class InsightGenerator:
    def generate_insights(self, analytics: dict[str, Any]) -> list[str]:
        insights: list[str] = []
        sections = safe_dict(analytics.get("sections"))
        executive = safe_dict(analytics.get("executive_summary"))
        records_count = safe_int(safe_dict(sections.get("storage", {})).get("records_count"), 0)
        if records_count <= 0:
            insights.append("No persisted records found yet. Run a workflow with persistence enabled.")
        token_section = safe_dict(sections.get("tokens"))
        if safe_int(token_section.get("estimated_records"), 0) > 0:
            insights.append("Some token usage records are estimated rather than provider-reported.")
        cost_section = safe_dict(sections.get("costs"))
        if safe_int(cost_section.get("unknown_pricing_records"), 0) > 0:
            insights.append("Cost tracking is available but pricing is unknown for some models.")
        workflow_section = safe_dict(sections.get("workflows"))
        if safe_int(workflow_section.get("failed_workflows"), 0) > 0:
            insights.append("Failed workflows were detected in recent activity.")
        governance_section = safe_dict(sections.get("governance"))
        if safe_int(governance_section.get("warning_count"), 0) > 0:
            insights.append("Governance warnings appear in recent workflow outputs.")
        brand_breakdown = safe_dict(sections.get("brand_breakdown"))
        if brand_breakdown:
            top_brand = self._top_group(brand_breakdown)
            if top_brand:
                insights.append(f"Most activity is associated with {top_brand}.")
        platform_breakdown = safe_dict(sections.get("platform_breakdown"))
        if platform_breakdown:
            top_platform = self._top_group(platform_breakdown)
            if top_platform:
                insights.append(f"Most generated content is for {top_platform}.")
        if not insights and safe_text(executive.get("headline"), limit=120):
            insights.append(safe_text(executive.get("headline"), limit=120))
        return list(dict.fromkeys(insights))

    def generate_recommendations(self, analytics: dict[str, Any]) -> list[str]:
        recommendations: list[str] = []
        sections = safe_dict(analytics.get("sections"))
        if safe_int(safe_dict(sections.get("storage", {})).get("records_count"), 0) <= 0:
            recommendations.extend(
                [
                    "Run a workflow with persistence enabled.",
                    "Generate content with report enabled.",
                    "Check storage records.",
                    "Review token/cost tracking.",
                ]
            )
        if safe_int(safe_dict(sections.get("workflows", {})).get("failed_workflows"), 0) > 0:
            recommendations.append("Review workflow failures and tighten the first failing step.")
        if safe_int(safe_dict(sections.get("costs", {})).get("unknown_pricing_records"), 0) > 0:
            recommendations.append("Update the pricing registry for unknown models to improve cost accuracy.")
        if safe_int(safe_dict(sections.get("governance", {})).get("warning_count"), 0) > 0:
            recommendations.append("Review governance warnings before exporting client-facing reports.")
        if not recommendations:
            recommendations.append("Continue running monitored workflows to build a fuller analytics baseline.")
        return list(dict.fromkeys(recommendations))

    def _top_group(self, group_payload: dict[str, Any]) -> str:
        groups = safe_dict(group_payload.get("groups"))
        if not groups:
            return ""
        top = max(groups.items(), key=lambda item: item[1])
        return safe_text(top[0], limit=80)
