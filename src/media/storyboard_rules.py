"""Storyboard rules for short-form video planning."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


STORYBOARD_RULES: dict[str, dict[str, Any]] = {
    "strong_first_3_seconds": {
        "description": "Use an immediate visual hook in the first three seconds.",
        "rule_fragment": "Start with a strong visual hook immediately.",
        "compatible_video_types": ["instagram_reel", "property_walkthrough", "campaign_teaser", "tiktok_video", "youtube_short"],
        "compatible_platforms": ["instagram", "tiktok", "facebook", "youtube"],
    },
    "visual_hook_before_context": {
        "description": "Show the visual idea before adding context.",
        "rule_fragment": "Lead with visuals before explanations.",
        "compatible_video_types": ["instagram_reel", "property_walkthrough", "lifestyle_video", "tiktok_video", "youtube_short"],
        "compatible_platforms": ["instagram", "tiktok", "facebook", "youtube"],
    },
    "one_message_per_scene": {
        "description": "Keep every scene focused on one message.",
        "rule_fragment": "One message per scene.",
        "compatible_video_types": list(STORYBOARD_RULES.keys()) if False else ["instagram_reel", "property_walkthrough", "lifestyle_video", "neighborhood_spotlight", "reform_opportunity_video", "relocation_video", "brand_story_video"],
        "compatible_platforms": ["instagram", "tiktok", "facebook", "youtube", "website", "linkedin"],
    },
    "short_voiceover_lines": {
        "description": "Keep voiceover lines short and production-friendly.",
        "rule_fragment": "Use short voiceover lines.",
        "compatible_video_types": ["instagram_reel", "tiktok_video", "youtube_short", "facebook_reel", "campaign_teaser"],
        "compatible_platforms": ["instagram", "tiktok", "facebook", "youtube"],
    },
    "platform_safe_cta": {
        "description": "Use a safe CTA that suits the platform.",
        "rule_fragment": "End with a platform-safe CTA.",
        "compatible_video_types": ["instagram_reel", "property_walkthrough", "relocation_video", "neighborhood_spotlight", "reform_opportunity_video", "brand_story_video"],
        "compatible_platforms": ["instagram", "tiktok", "facebook", "youtube", "website", "linkedin"],
    },
    "no_fake_urgency": {
        "description": "Avoid fake urgency and pressure language.",
        "rule_fragment": "Avoid fake urgency.",
        "compatible_video_types": ["instagram_reel", "property_walkthrough", "lifestyle_video", "neighborhood_spotlight", "reform_opportunity_video", "relocation_video", "brand_story_video"],
        "compatible_platforms": ["instagram", "tiktok", "facebook", "youtube", "website", "linkedin"],
    },
    "no_unverified_claims": {
        "description": "Avoid unsupported or invented claims.",
        "rule_fragment": "Avoid unverified claims.",
        "compatible_video_types": ["instagram_reel", "property_walkthrough", "lifestyle_video", "neighborhood_spotlight", "reform_opportunity_video", "relocation_video", "brand_story_video"],
        "compatible_platforms": ["instagram", "tiktok", "facebook", "youtube", "website", "linkedin"],
    },
    "location_context_without_hallucination": {
        "description": "Ground the script in real local context.",
        "rule_fragment": "Use location context without hallucination.",
        "compatible_video_types": ["neighborhood_spotlight", "relocation_video", "property_walkthrough", "brand_story_video"],
        "compatible_platforms": ["instagram", "facebook", "linkedin", "youtube", "website"],
    },
    "premium_but_approachable_tone": {
        "description": "Keep tone premium but approachable.",
        "rule_fragment": "Keep the tone premium but approachable.",
        "compatible_video_types": ["instagram_reel", "property_walkthrough", "lifestyle_video", "neighborhood_spotlight", "reform_opportunity_video", "relocation_video", "brand_story_video"],
        "compatible_platforms": ["instagram", "facebook", "linkedin", "youtube", "website", "tiktok"],
    },
    "natural_mallorca_lifestyle": {
        "description": "Show grounded Mediterranean lifestyle cues.",
        "rule_fragment": "Favor natural Mallorca lifestyle cues.",
        "compatible_video_types": ["property_walkthrough", "lifestyle_video", "neighborhood_spotlight", "relocation_video"],
        "compatible_platforms": ["instagram", "facebook", "youtube", "website"],
    },
    "clear_final_action": {
        "description": "End with a clear action step.",
        "rule_fragment": "End with a clear final action.",
        "compatible_video_types": ["instagram_reel", "property_walkthrough", "lifestyle_video", "neighborhood_spotlight", "reform_opportunity_video", "relocation_video", "brand_story_video"],
        "compatible_platforms": ["instagram", "tiktok", "facebook", "youtube", "website", "linkedin"],
    },
    "vertical_video_safe_framing": {
        "description": "Keep framing safe for vertical video crops.",
        "rule_fragment": "Use vertical-safe framing.",
        "compatible_video_types": ["instagram_reel", "tiktok_video", "youtube_short", "campaign_teaser"],
        "compatible_platforms": ["instagram", "tiktok", "youtube", "facebook"],
    },
    "cinematic_continuity": {
        "description": "Maintain a coherent visual flow across scenes.",
        "rule_fragment": "Preserve cinematic continuity.",
        "compatible_video_types": ["property_walkthrough", "lifestyle_video", "neighborhood_spotlight", "reform_opportunity_video", "brand_story_video", "cinematic_property_tour"],
        "compatible_platforms": ["instagram", "facebook", "youtube", "website"],
    },
}


def get_storyboard_rules() -> dict[str, dict[str, Any]]:
    """Return the storyboard rules."""

    return deepcopy(STORYBOARD_RULES)


def list_storyboard_rules() -> list[str]:
    """Return storyboard rule names."""

    return sorted(STORYBOARD_RULES.keys())


def resolve_storyboard_rules(video_type: str, platform: str) -> list[dict[str, Any]]:
    """Return rules compatible with a video type and platform."""

    video_key = str(video_type or "").strip().lower()
    platform_key = str(platform or "").strip().lower()
    rules: list[dict[str, Any]] = []
    for name, rule in STORYBOARD_RULES.items():
        if video_key and video_key not in rule["compatible_video_types"]:
            continue
        if platform_key and platform_key not in rule["compatible_platforms"]:
            continue
        cloned = deepcopy(rule)
        cloned["name"] = name
        rules.append(cloned)
    return rules
