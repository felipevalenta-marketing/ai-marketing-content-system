"""Campaign analytics for composition, sequence, and coverage."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import normalize_counts, safe_bool, safe_dict, safe_int, safe_list, safe_text, summarize_status_counts, unique_strings


class CampaignAnalytics:
    """Derive analytics from composed campaign packs."""

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Analyze a campaign payload."""

        campaign_result = safe_dict(payload.get("campaign_result"))
        if not campaign_result:
            campaign_result = safe_dict(payload)

        strategy = safe_dict(campaign_result.get("strategy"))
        asset_plan = safe_dict(campaign_result.get("asset_plan"))
        assets = safe_dict(campaign_result.get("assets"))
        platform_plan = safe_dict(campaign_result.get("platform_plan"))
        content_sequence = safe_list(campaign_result.get("content_sequence"))
        governance_summary = safe_dict(campaign_result.get("governance_summary"))

        asset_types = list(assets.keys())
        platforms = list(platform_plan.keys())
        deliverables = [safe_text(item.get("asset_type", ""), limit=80) for item in content_sequence if isinstance(item, dict)]
        cta_strategy = safe_text(strategy.get("cta_strategy") or campaign_result.get("cta_strategy", ""), limit=120)
        complexity = self._estimate_complexity(len(asset_types), len(platforms), len(content_sequence))

        return {
            "campaign_name": safe_text(campaign_result.get("campaign_name") or payload.get("campaign_name") or "", limit=120),
            "campaign_type": safe_text(campaign_result.get("campaign_type") or payload.get("campaign_type") or "", limit=80),
            "objective": safe_text(campaign_result.get("objective") or payload.get("objective") or "", limit=80),
            "brand": safe_text(campaign_result.get("brand") or payload.get("brand") or "", limit=80),
            "audience": safe_text(campaign_result.get("audience") or payload.get("audience") or "", limit=120),
            "location": safe_text(campaign_result.get("location") or payload.get("location") or "", limit=120),
            "platform_count": len(platforms),
            "platforms": platforms,
            "asset_count": len(asset_types),
            "asset_types": asset_types,
            "sequence_count": len(content_sequence),
            "content_sequence_steps": [safe_text(item.get("step", ""), limit=80) for item in content_sequence if isinstance(item, dict)],
            "cta_strategy": cta_strategy,
            "generated_deliverables": unique_strings(deliverables),
            "deliverable_count": len(unique_strings(deliverables)),
            "complexity": complexity,
            "governance_status": safe_text(governance_summary.get("status", "unknown"), limit=80),
            "governance_warning_count": safe_int(governance_summary.get("warning_assets"), 0),
            "governance_error_count": safe_int(governance_summary.get("rejected_assets"), 0),
            "asset_status_counts": summarize_status_counts(list(assets.values())),
            "platform_distribution": normalize_counts(platforms),
            "success": safe_bool(campaign_result.get("success")),
        }

    def _estimate_complexity(self, asset_count: int, platform_count: int, sequence_count: int) -> str:
        if asset_count >= 8 or platform_count >= 4 or sequence_count >= 5:
            return "high"
        if asset_count >= 4 or platform_count >= 3 or sequence_count >= 3:
            return "medium"
        return "low"
