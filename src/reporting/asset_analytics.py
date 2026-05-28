"""Asset analytics for creative planning and readiness."""

from __future__ import annotations

from typing import Any

from src.assets.asset_contracts import normalize_asset_type
from src.reporting.report_metrics import normalize_counts, safe_bool, safe_dict, safe_int, safe_list, safe_text, unique_strings


class AssetAnalytics:
    """Derive analytics from asset coordination results."""

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Analyze an asset coordination payload."""

        asset_result = safe_dict(payload.get("asset_coordination_result"))
        if not asset_result:
            asset_result = safe_dict(payload.get("asset_result"))
        if not asset_result:
            asset_result = safe_dict(payload)

        asset_plan = safe_dict(asset_result.get("asset_plan"))
        asset_requirements = safe_dict(asset_result.get("asset_requirements"))
        assets = safe_dict(asset_result.get("assets"))
        missing_assets = unique_strings(asset_result.get("missing_assets", []))
        validation_result = safe_dict(asset_result.get("validation_result"))
        platform_mapping = safe_dict(asset_plan.get("platform_mapping"))

        asset_types = [normalize_asset_type(name) for name in list(assets.keys())]
        image_prompt_count = sum(1 for item in asset_types if item == "image_prompt")
        video_prompt_count = sum(1 for item in asset_types if item == "video_prompt")
        export_ready_count = sum(1 for asset in assets.values() if isinstance(asset, dict) and safe_text(asset.get("status", "")).lower() in {"approved", "warning", "ready"})
        platform_distribution = normalize_counts(list(platform_mapping.keys()))

        return {
            "brand": safe_text(asset_result.get("brand") or payload.get("brand") or "", limit=80),
            "campaign_type": safe_text(asset_result.get("campaign_type") or payload.get("campaign_type") or "", limit=80),
            "objective": safe_text(asset_result.get("objective") or payload.get("objective") or "", limit=80),
            "asset_count": len(assets),
            "asset_types": asset_types,
            "image_prompt_count": image_prompt_count,
            "video_prompt_count": video_prompt_count,
            "export_ready_count": export_ready_count,
            "missing_asset_count": len(missing_assets),
            "missing_assets": missing_assets,
            "platform_distribution": platform_distribution,
            "platform_mapping_count": len(platform_mapping),
            "requirement_sections": list(asset_requirements.keys()),
            "validation_valid": safe_bool(validation_result.get("valid", asset_result.get("success", False))),
            "validation_warning_count": len(safe_list(validation_result.get("warnings"))),
            "validation_error_count": len(safe_list(validation_result.get("errors"))),
            "success": safe_bool(asset_result.get("success")),
        }
