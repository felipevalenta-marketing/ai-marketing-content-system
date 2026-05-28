"""Reusable negative prompt groups for image prompt generation."""

from __future__ import annotations

from typing import Any


NEGATIVE_PROMPT_GROUPS: dict[str, list[str]] = {
    "general": [
        "low quality",
        "blurry",
        "pixelated",
        "distorted",
        "watermark",
        "text artifacts",
        "oversaturated",
        "unrealistic lighting",
        "cartoon",
        "CGI look",
    ],
    "real_estate": [
        "fake luxury",
        "unrealistic architecture",
        "distorted interiors",
        "impossible rooms",
        "exaggerated scale",
        "cluttered composition",
        "fantasy architecture",
        "artificial materials",
    ],
    "people_lifestyle": [
        "distorted faces",
        "extra limbs",
        "unnatural posture",
        "artificial expressions",
    ],
}

STYLE_SPECIFIC_NEGATIVE_PROMPTS: dict[str, list[str]] = {
    "luxury_editorial": ["overly glossy", "sterile showroom look"],
    "mediterranean_lifestyle": ["tourist postcard look", "fake beach view"],
    "minimal_architecture": ["ornate clutter", "busy composition"],
    "premium_interior": ["plastic materials", "overscaled furniture"],
    "sunset_real_estate": ["neon sunset", "overprocessed sky"],
    "coastal_premium": ["tropical resort look", "caricature coastline"],
    "modern_mallorca": ["futuristic glass tower", "city skyline"],
    "rustic_mediterranean": ["rustic cartoon style", "muddy textures"],
    "natural_light_editorial": ["flat lighting", "harsh flash"],
}


def build_negative_prompt(image_type: str, platform: str, visual_style: str = "") -> str:
    """Build a deterministic negative prompt for a request."""

    image_key = str(image_type or "").strip().lower()
    platform_key = str(platform or "").strip().lower()
    style_key = str(visual_style or "").strip().lower()

    terms: list[str] = []
    terms.extend(NEGATIVE_PROMPT_GROUPS["general"])
    terms.extend(NEGATIVE_PROMPT_GROUPS["real_estate"])
    if image_key in {"lifestyle_scene", "social_media_visual", "campaign_hero_image", "neighborhood_scene"}:
        terms.extend(NEGATIVE_PROMPT_GROUPS["people_lifestyle"])
    terms.extend(STYLE_SPECIFIC_NEGATIVE_PROMPTS.get(style_key, []))
    if platform_key in {"linkedin", "website", "luxury_listing_portal"}:
        terms.append("overly emotional")
    if platform_key in {"instagram", "facebook"}:
        terms.append("hard sell")

    deduped = list(dict.fromkeys([term for term in terms if term]))
    return ", ".join(deduped)


def get_negative_prompt_groups() -> dict[str, list[str]]:
    """Return the negative prompt groups."""

    return {key: list(value) for key, value in NEGATIVE_PROMPT_GROUPS.items()}
