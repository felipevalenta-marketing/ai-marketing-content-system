"""Reusable scene templates for structured video scripts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


SCENE_TEMPLATES: dict[str, dict[str, Any]] = {
    "property_launch": {
        "name": "property_launch",
        "scene_count": 5,
        "scene_purposes": [
            "Hook / first impression",
            "Exterior or lifestyle context",
            "Main property value",
            "Location or lifestyle relevance",
            "CTA",
        ],
        "recommended_duration_distribution": [0.16, 0.20, 0.24, 0.20, 0.20],
        "visual_roles": ["hook", "context", "value", "location", "cta"],
        "cta_position": "final_scene",
        "hook_style": "visual-first property reveal",
    },
    "relocation_video": {
        "name": "relocation_video",
        "scene_count": 5,
        "scene_purposes": [
            "Relocation problem",
            "Mallorca lifestyle context",
            "Neighborhood/property fit",
            "Trust-building message",
            "CTA",
        ],
        "recommended_duration_distribution": [0.18, 0.20, 0.22, 0.18, 0.22],
        "visual_roles": ["problem", "lifestyle", "fit", "trust", "cta"],
        "cta_position": "final_scene",
        "hook_style": "empathetic relocation entry point",
    },
    "neighborhood_spotlight": {
        "name": "neighborhood_spotlight",
        "scene_count": 5,
        "scene_purposes": [
            "Area hook",
            "Local lifestyle",
            "Accessibility/infrastructure",
            "Property opportunity",
            "CTA",
        ],
        "recommended_duration_distribution": [0.18, 0.20, 0.20, 0.18, 0.24],
        "visual_roles": ["area", "lifestyle", "access", "opportunity", "cta"],
        "cta_position": "final_scene",
        "hook_style": "local discovery opener",
    },
    "reform_opportunity_video": {
        "name": "reform_opportunity_video",
        "scene_count": 5,
        "scene_purposes": [
            "Opportunity hook",
            "Current property character",
            "Reform potential",
            "Practical considerations",
            "CTA",
        ],
        "recommended_duration_distribution": [0.18, 0.20, 0.22, 0.18, 0.22],
        "visual_roles": ["opportunity", "character", "potential", "practicality", "cta"],
        "cta_position": "final_scene",
        "hook_style": "value-add opener",
    },
    "brand_story_video": {
        "name": "brand_story_video",
        "scene_count": 5,
        "scene_purposes": [
            "Brand promise",
            "Local expertise",
            "Client journey",
            "Trust and service",
            "CTA",
        ],
        "recommended_duration_distribution": [0.16, 0.20, 0.20, 0.20, 0.24],
        "visual_roles": ["promise", "expertise", "journey", "service", "cta"],
        "cta_position": "final_scene",
        "hook_style": "trust-building brand introduction",
    },
}

VIDEO_TYPE_TO_TEMPLATE = {
    "instagram_reel": "property_launch",
    "property_walkthrough": "property_launch",
    "lifestyle_video": "property_launch",
    "neighborhood_spotlight": "neighborhood_spotlight",
    "reform_opportunity_video": "reform_opportunity_video",
    "relocation_video": "relocation_video",
    "campaign_teaser": "brand_story_video",
    "listing_highlight": "property_launch",
    "brand_story_video": "brand_story_video",
    "youtube_short": "property_launch",
    "tiktok_video": "property_launch",
    "paid_ad_video": "brand_story_video",
    "website_hero_video": "brand_story_video",
    "cinematic_property_tour": "property_launch",
    "client_testimonial_script": "brand_story_video",
    "voiceover_ad": "brand_story_video",
}


def get_scene_template(name: str) -> dict[str, Any]:
    """Return a scene template, falling back to a property-launch structure."""

    key = str(name or "").strip().lower().replace(" ", "_")
    alias = VIDEO_TYPE_TO_TEMPLATE.get(key, key)
    template = SCENE_TEMPLATES.get(alias) or SCENE_TEMPLATES["property_launch"]
    return deepcopy(template)


def resolve_scene_template(request: dict[str, Any]) -> dict[str, Any]:
    """Resolve a scene template from a request payload."""

    candidate = str(request.get("campaign_type") or request.get("video_type") or "").strip().lower()
    return get_scene_template(candidate)


def list_scene_templates() -> list[str]:
    """Return the registered template names."""

    return sorted(SCENE_TEMPLATES.keys())
