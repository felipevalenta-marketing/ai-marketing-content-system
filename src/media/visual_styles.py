"""Reusable visual style presets for image prompt generation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


VISUAL_STYLES: dict[str, dict[str, Any]] = {
    "luxury_editorial": {
        "name": "luxury_editorial",
        "mood": "premium, calm, editorial",
        "lighting": "natural window light with soft contrast",
        "composition": "balanced editorial framing with strong negative space",
        "texture": "refined stone, wood, linen, brushed metal",
        "color_palette": "warm neutrals, stone, cream, muted taupe",
        "lens": "35mm architectural photography",
        "atmosphere": "polished but believable",
        "rendering_quality": "high-end realistic photography",
        "best_for": ["luxury_listing", "campaign_hero_image", "property_interior"],
    },
    "mediterranean_lifestyle": {
        "name": "mediterranean_lifestyle",
        "mood": "sunlit, relaxed, aspirational",
        "lighting": "natural daylight with gentle warmth",
        "composition": "open, airy framing with lifestyle emphasis",
        "texture": "limewash, timber, terracotta, woven fabrics",
        "color_palette": "sand, ivory, terracotta, sea blue accents",
        "lens": "35mm lifestyle real estate photography",
        "atmosphere": "authentic Mediterranean calm",
        "rendering_quality": "realistic premium photography",
        "best_for": ["property_exterior", "lifestyle_scene", "neighborhood_scene", "social_media_visual"],
    },
    "minimal_architecture": {
        "name": "minimal_architecture",
        "mood": "clean, precise, understated",
        "lighting": "soft even daylight",
        "composition": "symmetry, clean lines, restrained framing",
        "texture": "smooth plaster, glass, stone, matte metal",
        "color_palette": "white, grey, black, muted natural tones",
        "lens": "24-35mm architecture lens",
        "atmosphere": "quietly premium and structured",
        "rendering_quality": "architectural photography realism",
        "best_for": ["architectural_detail", "property_exterior", "luxury_listing"],
    },
    "premium_interior": {
        "name": "premium_interior",
        "mood": "warm, elevated, welcoming",
        "lighting": "soft interior daylight with realistic shadows",
        "composition": "layered interior staging with depth",
        "texture": "oak, linen, stone, ceramic, soft upholstery",
        "color_palette": "warm white, oak, beige, muted olive",
        "lens": "24-35mm interior photography",
        "atmosphere": "livable luxury",
        "rendering_quality": "realistic interior editorial",
        "best_for": ["property_interior", "luxury_listing", "campaign_hero_image"],
    },
    "sunset_real_estate": {
        "name": "sunset_real_estate",
        "mood": "warm, cinematic, calm",
        "lighting": "golden hour sunset with soft highlights",
        "composition": "hero framing with gentle depth",
        "texture": "warm stucco, natural stone, glass reflections",
        "color_palette": "amber, coral, sand, muted blue",
        "lens": "35mm cinematic real estate",
        "atmosphere": "evening serenity",
        "rendering_quality": "realistic sunset photography",
        "best_for": ["property_exterior", "drone_view", "campaign_hero_image"],
    },
    "coastal_premium": {
        "name": "coastal_premium",
        "mood": "fresh, luminous, coastal",
        "lighting": "bright natural coastal light",
        "composition": "open composition with horizon balance",
        "texture": "light wood, sea glass, limestone, fabric textures",
        "color_palette": "white, sand, sea blue, pale green",
        "lens": "35mm coastal editorial lens",
        "atmosphere": "premium coastal calm",
        "rendering_quality": "photorealistic coastal property imagery",
        "best_for": ["neighborhood_scene", "lifestyle_scene", "property_exterior"],
    },
    "modern_mallorca": {
        "name": "modern_mallorca",
        "mood": "contemporary, local, refined",
        "lighting": "bright daylight with clean contrast",
        "composition": "balanced modern architecture framing",
        "texture": "stone, glass, timber, matte plaster",
        "color_palette": "warm white, grey stone, olive, muted blue",
        "lens": "24-35mm modern architecture lens",
        "atmosphere": "Mallorca modern living",
        "rendering_quality": "realistic premium architecture",
        "best_for": ["property_exterior", "architectural_detail", "luxury_listing"],
    },
    "rustic_mediterranean": {
        "name": "rustic_mediterranean",
        "mood": "grounded, inviting, timeless",
        "lighting": "soft daylight with natural shadow detail",
        "composition": "honest, lived-in framing with texture focus",
        "texture": "stone, plaster, aged timber, terracotta",
        "color_palette": "earth tones, cream, warm clay, olive",
        "lens": "35mm documentary real estate lens",
        "atmosphere": "authentic rural elegance",
        "rendering_quality": "believable Mediterranean realism",
        "best_for": ["property_exterior", "reform_potential", "neighborhood_scene"],
    },
    "natural_light_editorial": {
        "name": "natural_light_editorial",
        "mood": "bright, clean, premium",
        "lighting": "natural light with soft editorial polish",
        "composition": "well-balanced with strong clarity",
        "texture": "natural materials with tactile detail",
        "color_palette": "light neutrals, stone, wood, soft blue",
        "lens": "35mm editorial photography",
        "atmosphere": "clear and aspirational",
        "rendering_quality": "high realism with editorial finish",
        "best_for": ["social_media_visual", "property_interior", "campaign_hero_image"],
    },
}

DEFAULT_VISUAL_STYLE = "mediterranean_lifestyle"


def get_visual_style(name: str) -> dict[str, Any]:
    """Return a visual style preset."""

    key = str(name or "").strip().lower().replace(" ", "_")
    return deepcopy(VISUAL_STYLES.get(key, VISUAL_STYLES[DEFAULT_VISUAL_STYLE]))


def list_visual_styles() -> list[str]:
    """Return all supported visual styles."""

    return sorted(VISUAL_STYLES.keys())
