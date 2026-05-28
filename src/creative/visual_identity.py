"""Reusable visual identity profiles for creative direction."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_VISUAL_IDENTITY = "mediterranean_luxury"


VISUAL_IDENTITIES: dict[str, dict[str, Any]] = {
    "mediterranean_luxury": {
        "name": "mediterranean_luxury",
        "visual_keywords": ["Mediterranean", "premium", "architectural", "refined", "sunlit"],
        "mood": "premium, calm, and elevated",
        "texture": "natural stone, warm plaster, timber, linen",
        "lighting": "natural daylight with warm highlights and soft interior shadow",
        "composition": "editorial framing with balanced geometry and breathing room",
        "camera_style": "steady, composed, and quietly cinematic",
        "color_palette": "mediterranean_neutrals",
        "best_for": ["property_launch_direction", "luxury_listing_direction", "campaign_visual_direction"],
    },
    "premium_approachable": {
        "name": "premium_approachable",
        "visual_keywords": ["premium", "human", "warm", "clear", "trustworthy"],
        "mood": "premium but approachable",
        "texture": "warm materials and lived-in polish",
        "lighting": "natural light with gentle contrast",
        "composition": "clean, welcoming, and easy to read",
        "camera_style": "steady and human, with subtle editorial polish",
        "color_palette": "premium_soft_contrast",
        "best_for": ["brand_awareness_direction", "relocation_campaign_direction", "social_campaign_direction"],
    },
    "natural_mallorca_lifestyle": {
        "name": "natural_mallorca_lifestyle",
        "visual_keywords": ["Mallorca", "outdoor", "authentic", "relaxed", "warm"],
        "mood": "grounded Mediterranean lifestyle",
        "texture": "sun-warmed stone, organic fabrics, greenery",
        "lighting": "sunlit, airy, and naturally balanced",
        "composition": "lifestyle-forward with clear spatial context",
        "camera_style": "gentle and observational",
        "color_palette": "natural_light_palette",
        "best_for": ["relocation_campaign_direction", "neighborhood_spotlight_direction", "lifestyle_campaign_direction"],
    },
    "editorial_real_estate": {
        "name": "editorial_real_estate",
        "visual_keywords": ["editorial", "architectural", "clean", "balanced", "trustworthy"],
        "mood": "polished and informed",
        "texture": "architectural surfaces and tactile detail",
        "lighting": "soft daylight with controlled contrast",
        "composition": "architectural editorial framing",
        "camera_style": "structured, precise, and steady",
        "color_palette": "palma_editorial",
        "best_for": ["campaign_visual_direction", "brand_awareness_direction", "editorial_campaign_direction"],
    },
    "rustic_modern_comfort": {
        "name": "rustic_modern_comfort",
        "visual_keywords": ["rustic", "modern comfort", "balanced", "warm", "grounded"],
        "mood": "comfortable and authentic",
        "texture": "stone, wood, matte finishes, soft textiles",
        "lighting": "warm daylight and soft ambient interior light",
        "composition": "balanced rustic-modern contrast",
        "camera_style": "steady and warm with practical clarity",
        "color_palette": "rustic_earth_tones",
        "best_for": ["property_launch_direction", "reform_opportunity_direction", "lifestyle_campaign_direction"],
    },
    "coastal_refined": {
        "name": "coastal_refined",
        "visual_keywords": ["coastal", "refined", "bright", "fresh", "premium"],
        "mood": "calm coastal refinement",
        "texture": "limewashed walls, pale wood, light stone",
        "lighting": "soft coastal daylight",
        "composition": "fresh and spacious",
        "camera_style": "light, clean, and balanced",
        "color_palette": "coastal_blue_and_white",
        "best_for": ["lifestyle_campaign_direction", "luxury_listing_direction", "campaign_visual_direction"],
    },
    "urban_palma_editorial": {
        "name": "urban_palma_editorial",
        "visual_keywords": ["urban", "Palma", "editorial", "architectural", "connected"],
        "mood": "smart urban sophistication",
        "texture": "stone, glass, steel, polished surfaces",
        "lighting": "clean daylight with architectural contrast",
        "composition": "city-forward editorial framing",
        "camera_style": "precise and contemporary",
        "color_palette": "palma_editorial",
        "best_for": ["brand_awareness_direction", "editorial_campaign_direction"],
    },
    "investment_confidence": {
        "name": "investment_confidence",
        "visual_keywords": ["trust", "clarity", "value", "calm", "professional"],
        "mood": "measured confidence",
        "texture": "clean surfaces and restrained premium detail",
        "lighting": "neutral daylight with minimal flourish",
        "composition": "clear and informative",
        "camera_style": "stable, direct, and credible",
        "color_palette": "mediterranean_neutrals",
        "best_for": ["reform_opportunity_direction", "paid_ads_direction", "investment-focused campaigns"],
    },
    "relocation_warmth": {
        "name": "relocation_warmth",
        "visual_keywords": ["relocation", "welcome", "family", "ease", "practical"],
        "mood": "reassuring and welcoming",
        "texture": "soft textiles, warm stone, human-scale interiors",
        "lighting": "warm daylight and inviting interior warmth",
        "composition": "clear, family-friendly, and reassuring",
        "camera_style": "gentle and supportive",
        "color_palette": "warm_stone_and_sand",
        "best_for": ["relocation_campaign_direction", "brand_awareness_direction", "social_campaign_direction"],
    },
}


def get_visual_identity(name: str) -> dict[str, Any]:
    """Return a visual identity profile, falling back to a premium default."""

    key = str(name or "").strip().lower().replace(" ", "_")
    return deepcopy(VISUAL_IDENTITIES.get(key, VISUAL_IDENTITIES[DEFAULT_VISUAL_IDENTITY]))


def list_visual_identities() -> list[str]:
    """Return registered visual identity names."""

    return sorted(VISUAL_IDENTITIES.keys())
