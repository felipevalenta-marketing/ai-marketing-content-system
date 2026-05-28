"""Moodboard rules for consistent creative direction."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


MOODBOARD_RULES: dict[str, dict[str, Any]] = {
    "warm_mediterranean_light": {
        "description": "Use warm Mediterranean light with soft highlights.",
        "visual_fragment": "warm Mediterranean daylight and gentle highlights",
        "compatible_campaign_types": ["property_launch", "lifestyle_campaign", "neighborhood_spotlight", "reform_opportunity"],
        "compatible_platforms": ["instagram", "facebook", "linkedin", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "campaign_bundle"],
    },
    "natural_materials": {
        "description": "Show natural materials and tactile finishes.",
        "visual_fragment": "stone, timber, linen, plaster, and grounded texture",
        "compatible_campaign_types": ["property_launch", "reform_opportunity", "brand_awareness"],
        "compatible_platforms": ["instagram", "facebook", "linkedin", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "website_listing"],
    },
    "architectural_calm": {
        "description": "Keep the visual rhythm calm and architectural.",
        "visual_fragment": "clean architecture, composed framing, and spatial calm",
        "compatible_campaign_types": ["property_launch", "brand_awareness", "investment_angle"],
        "compatible_platforms": ["instagram", "linkedin", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "campaign_bundle"],
    },
    "premium_but_human": {
        "description": "Keep the brand premium but human.",
        "visual_fragment": "premium detail balanced with approachable warmth",
        "compatible_campaign_types": ["relocation_campaign", "brand_awareness", "lifestyle_campaign"],
        "compatible_platforms": ["instagram", "facebook", "linkedin", "email", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "social_post"],
    },
    "editorial_composition": {
        "description": "Use editorial composition with breathing room.",
        "visual_fragment": "editorial composition with clear subject hierarchy",
        "compatible_campaign_types": ["property_launch", "luxury_listing", "brand_awareness"],
        "compatible_platforms": ["instagram", "linkedin", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "campaign_hero_image"],
    },
    "indoor_outdoor_lifestyle": {
        "description": "Show indoor-outdoor flow and lifestyle continuity.",
        "visual_fragment": "seamless indoor-outdoor lifestyle flow",
        "compatible_campaign_types": ["lifestyle_campaign", "neighborhood_spotlight", "property_launch"],
        "compatible_platforms": ["instagram", "facebook", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "story_sequence"],
    },
    "grounded_luxury": {
        "description": "Express luxury through restraint and realism.",
        "visual_fragment": "grounded luxury with restrained premium detail",
        "compatible_campaign_types": ["luxury_listing", "property_launch", "campaign_visual_direction"],
        "compatible_platforms": ["instagram", "linkedin", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "campaign_hero_image"],
    },
    "reform_potential_realism": {
        "description": "Show honest reform potential without fantasy.",
        "visual_fragment": "realistic reform potential with clear before/after logic",
        "compatible_campaign_types": ["reform_opportunity", "investment_angle"],
        "compatible_platforms": ["instagram", "linkedin", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "landing_page_copy"],
    },
    "relocation_reassurance": {
        "description": "Reassure relocation buyers with clarity and ease.",
        "visual_fragment": "reassuring relocation warmth and practical clarity",
        "compatible_campaign_types": ["relocation_campaign", "brand_awareness"],
        "compatible_platforms": ["instagram", "facebook", "linkedin", "email"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "email_teaser"],
    },
    "coastal_lifestyle_energy": {
        "description": "Bring a clean coastal lifestyle energy.",
        "visual_fragment": "coastal lifestyle energy with fresh premium tone",
        "compatible_campaign_types": ["lifestyle_campaign", "neighborhood_spotlight", "seasonal_campaign"],
        "compatible_platforms": ["instagram", "facebook", "website"],
        "compatible_asset_types": ["image_prompt", "video_prompt", "social_post"],
    },
}


def get_moodboard_rules() -> dict[str, dict[str, Any]]:
    """Return the moodboard rules."""

    return deepcopy(MOODBOARD_RULES)


def list_moodboard_rules() -> list[str]:
    """Return rule names."""

    return sorted(MOODBOARD_RULES.keys())


def resolve_moodboard_rules(campaign_type: str, platform: str, asset_types: list[str] | None = None) -> list[dict[str, Any]]:
    """Return rules compatible with the given inputs."""

    campaign_key = str(campaign_type or "").strip().lower()
    platform_key = str(platform or "").strip().lower()
    asset_keys = {str(asset or "").strip().lower() for asset in (asset_types or []) if str(asset or "").strip()}
    rules: list[dict[str, Any]] = []
    for name, rule in MOODBOARD_RULES.items():
        if campaign_key and campaign_key not in rule["compatible_campaign_types"] and campaign_key.replace("_direction", "") not in rule["compatible_campaign_types"]:
            continue
        if platform_key and platform_key not in rule["compatible_platforms"]:
            continue
        if asset_keys and asset_keys.isdisjoint({str(asset or "").strip().lower() for asset in rule["compatible_asset_types"]}):
            continue
        cloned = deepcopy(rule)
        cloned["name"] = name
        rules.append(cloned)
    return rules
