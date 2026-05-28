"""Cinematic composition rules for image prompt generation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CINEMATIC_RULES: dict[str, dict[str, Any]] = {
    "rule_of_thirds": {
        "description": "Place the subject using the rule of thirds for stronger visual balance.",
        "prompt_fragment": "Compose with the rule of thirds for balanced visual tension.",
        "compatible_image_types": ["property_exterior", "lifestyle_scene", "social_media_visual", "campaign_hero_image"],
        "compatible_platforms": ["instagram", "facebook", "website", "luxury_listing_portal"],
    },
    "architectural_symmetry": {
        "description": "Use symmetrical architectural framing for a premium, orderly feel.",
        "prompt_fragment": "Use symmetrical architectural framing and centered structure.",
        "compatible_image_types": ["architectural_detail", "property_exterior", "luxury_listing", "campaign_hero_image"],
        "compatible_platforms": ["linkedin", "website", "luxury_listing_portal"],
    },
    "natural_depth_of_field": {
        "description": "Add believable depth of field with realistic focus falloff.",
        "prompt_fragment": "Use a natural depth of field with realistic focus falloff.",
        "compatible_image_types": ["property_interior", "property_exterior", "lifestyle_scene", "neighborhood_scene"],
        "compatible_platforms": ["instagram", "facebook", "website", "luxury_listing_portal"],
    },
    "golden_hour_lighting": {
        "description": "Describe warm late-day lighting for a premium cinematic mood.",
        "prompt_fragment": "Capture golden hour lighting with warm, realistic highlights.",
        "compatible_image_types": ["property_exterior", "drone_view", "campaign_hero_image", "lifestyle_scene"],
        "compatible_platforms": ["instagram", "facebook", "website"],
    },
    "soft_shadow_realism": {
        "description": "Keep shadows soft and physically believable.",
        "prompt_fragment": "Preserve soft shadow realism with physically believable contrast.",
        "compatible_image_types": ["property_interior", "property_exterior", "architectural_detail", "luxury_listing"],
        "compatible_platforms": ["instagram", "linkedin", "website", "luxury_listing_portal"],
    },
    "editorial_real_estate_composition": {
        "description": "Frame the image like a premium real estate editorial.",
        "prompt_fragment": "Use editorial real estate composition with clean lines and spacious framing.",
        "compatible_image_types": ["luxury_listing", "campaign_hero_image", "social_media_visual", "property_interior"],
        "compatible_platforms": ["instagram", "linkedin", "website", "luxury_listing_portal"],
    },
    "wide_angle_interior": {
        "description": "Use a wide-angle interior perspective without distortion.",
        "prompt_fragment": "Use a wide-angle interior perspective while keeping proportions realistic.",
        "compatible_image_types": ["property_interior", "reform_potential", "luxury_listing"],
        "compatible_platforms": ["instagram", "website", "luxury_listing_portal"],
    },
    "drone_perspective": {
        "description": "Use elevated aerial framing for site context and landscape.",
        "prompt_fragment": "Use a drone perspective with realistic altitude and clear property context.",
        "compatible_image_types": ["drone_view", "neighborhood_scene", "property_exterior", "campaign_hero_image"],
        "compatible_platforms": ["instagram", "website", "luxury_listing_portal"],
    },
    "lifestyle_subject_framing": {
        "description": "Frame any people or lifestyle cues naturally and authentically.",
        "prompt_fragment": "Frame lifestyle elements naturally, with authentic human scale and posture.",
        "compatible_image_types": ["lifestyle_scene", "social_media_visual", "campaign_hero_image"],
        "compatible_platforms": ["instagram", "facebook", "website"],
    },
    "premium_texture_detail": {
        "description": "Emphasize tactile materials and refined surface detail.",
        "prompt_fragment": "Highlight premium texture detail with believable material surfaces.",
        "compatible_image_types": ["property_interior", "property_exterior", "architectural_detail", "luxury_listing"],
        "compatible_platforms": ["linkedin", "website", "luxury_listing_portal"],
    },
}


def get_cinematic_rules() -> dict[str, dict[str, Any]]:
    """Return all cinematic rules."""

    return deepcopy(CINEMATIC_RULES)


def list_cinematic_rules() -> list[str]:
    """Return supported cinematic rule identifiers."""

    return sorted(CINEMATIC_RULES.keys())


def resolve_cinematic_rules(image_type: str, platform: str, visual_style: str = "") -> list[dict[str, Any]]:
    """Return compatible cinematic rules for a request."""

    image_key = str(image_type or "").strip().lower()
    platform_key = str(platform or "").strip().lower()
    selected: list[dict[str, Any]] = []
    for rule_name, rule in CINEMATIC_RULES.items():
        if image_key and image_key not in rule["compatible_image_types"]:
            continue
        if platform_key and platform_key not in rule["compatible_platforms"]:
            continue
        selected.append({"name": rule_name, **deepcopy(rule)})
    return selected
