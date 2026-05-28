"""Asset analytics for creative planning and readiness."""

from __future__ import annotations

from typing import Any

from src.assets.asset_contracts import normalize_asset_type
from src.reporting.report_metrics import normalize_counts, safe_bool, safe_dict, safe_float, safe_int, safe_list, safe_text, unique_strings


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
        image_prompt_result = safe_dict(asset_result.get("image_prompt_result"))
        if not image_prompt_result and isinstance(assets.get("image_prompt"), dict):
            image_prompt_result = safe_dict(assets.get("image_prompt"))
        video_script_result = safe_dict(asset_result.get("video_script_result"))
        if not video_script_result and isinstance(assets.get("reel_script"), dict):
            video_script_result = safe_dict(assets.get("reel_script"))

        asset_types = [normalize_asset_type(name) for name in list(assets.keys())]
        image_prompt_count = sum(1 for item in asset_types if item == "image_prompt")
        video_prompt_count = sum(1 for item in asset_types if item == "video_prompt")
        reel_script_count = sum(1 for item in asset_types if item == "reel_script")
        export_ready_count = sum(1 for asset in assets.values() if isinstance(asset, dict) and safe_text(asset.get("status", "")).lower() in {"approved", "warning", "ready"})
        platform_distribution = normalize_counts(list(platform_mapping.keys()))
        image_prompt_validation = safe_dict(image_prompt_result.get("validation"))
        image_prompt_scores = safe_dict(image_prompt_validation.get("scores"))
        video_script_validation = safe_dict(video_script_result.get("validation"))
        video_script_scores = safe_dict(video_script_validation.get("scores"))
        scene_sequence = safe_list(video_script_result.get("scene_sequence"))
        storyboard = safe_list(video_script_result.get("storyboard"))

        return {
            "brand": safe_text(asset_result.get("brand") or payload.get("brand") or "", limit=80),
            "campaign_type": safe_text(asset_result.get("campaign_type") or payload.get("campaign_type") or "", limit=80),
            "objective": safe_text(asset_result.get("objective") or payload.get("objective") or "", limit=80),
            "asset_count": len(assets),
            "asset_types": asset_types,
            "image_prompt_count": image_prompt_count,
            "video_prompt_count": video_prompt_count,
            "reel_script_count": reel_script_count,
            "export_ready_count": export_ready_count,
            "missing_asset_count": len(missing_assets),
            "missing_assets": missing_assets,
            "platform_distribution": platform_distribution,
            "platform_mapping_count": len(platform_mapping),
            "requirement_sections": list(asset_requirements.keys()),
            "image_type": safe_text(image_prompt_result.get("image_type") or payload.get("image_type") or "", limit=80),
            "aspect_ratio": safe_text(image_prompt_result.get("aspect_ratio") or payload.get("aspect_ratio") or "", limit=80),
            "visual_style_used": safe_text(image_prompt_result.get("visual_style") or payload.get("visual_style") or "", limit=80),
            "cinematic_rules_count": safe_int(len(safe_list(image_prompt_result.get("cinematic_rules_applied"))), 0),
            "negative_prompt_enabled": safe_bool(bool(image_prompt_result.get("negative_prompt"))),
            "image_prompt_validation_status": safe_bool(image_prompt_validation.get("valid", False)) if image_prompt_validation else False,
            "realism_score": safe_float(image_prompt_scores.get("realism"), 0.0),
            "completeness_score": safe_float(image_prompt_scores.get("completeness"), 0.0),
            "platform_fit_score": safe_float(image_prompt_scores.get("platform_fit"), 0.0),
            "conciseness_score": safe_float(image_prompt_scores.get("conciseness"), 0.0),
            "video_type": safe_text(video_script_result.get("video_type") or payload.get("video_type") or "", limit=80),
            "duration": safe_text(video_script_result.get("duration") or payload.get("duration") or "", limit=80),
            "scene_count": safe_int(len(scene_sequence), 0),
            "storyboard_scene_count": safe_int(len(storyboard), 0),
            "voiceover_length": safe_int(len(safe_text(video_script_result.get("voiceover") or "", limit=120).split()), 0),
            "hook_present": safe_bool(bool(safe_text(video_script_result.get("hook") or "", limit=120))),
            "cta_present": safe_bool(bool(safe_text(video_script_result.get("cta") or "", limit=120))),
            "validation_status": safe_bool(video_script_validation.get("valid", False)) if video_script_validation else False,
            "video_validation_status": safe_bool(video_script_validation.get("valid", False)) if video_script_validation else False,
            "pacing_score": safe_float(video_script_scores.get("pacing"), 0.0),
            "factual_safety_score": safe_float(video_script_scores.get("factual_safety"), 0.0),
            "video_realism_score": safe_float(video_script_scores.get("factual_safety"), 0.0),
            "video_brand_fit_score": safe_float(video_script_scores.get("brand_fit"), 0.0),
            "video_platform_fit_score": safe_float(video_script_scores.get("platform_fit"), 0.0),
            "validation_valid": safe_bool(validation_result.get("valid", asset_result.get("success", False))),
            "validation_warning_count": len(safe_list(validation_result.get("warnings"))),
            "validation_error_count": len(safe_list(validation_result.get("errors"))),
            "success": safe_bool(asset_result.get("success")),
        }
