"""Serialization-safe contracts for image prompt orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


SUPPORTED_IMAGE_PROMPT_TYPES = (
    "property_exterior",
    "property_interior",
    "lifestyle_scene",
    "architectural_detail",
    "drone_view",
    "neighborhood_scene",
    "reform_potential",
    "luxury_listing",
    "social_media_visual",
    "campaign_hero_image",
)

SUPPORTED_ASPECT_RATIOS = ("1:1", "4:5", "9:16", "16:9", "3:2")

SUPPORTED_PLATFORMS = ("instagram", "facebook", "linkedin", "website", "luxury_listing_portal")

PLATFORM_VISUAL_GUIDANCE: dict[str, dict[str, Any]] = {
    "instagram": {
        "preferred_aspect_ratios": ["4:5", "9:16"],
        "tone": "lifestyle-oriented and emotionally resonant",
        "visual_priority": "strong first impression",
    },
    "facebook": {
        "preferred_aspect_ratios": ["4:5", "1:1"],
        "tone": "warm and accessible",
        "visual_priority": "human and approachable",
    },
    "linkedin": {
        "preferred_aspect_ratios": ["16:9", "1:1"],
        "tone": "professional and strategic",
        "visual_priority": "clean and architectural",
    },
    "website": {
        "preferred_aspect_ratios": ["16:9", "3:2", "4:5"],
        "tone": "factual and listing-ready",
        "visual_priority": "clear and informative",
    },
    "luxury_listing_portal": {
        "preferred_aspect_ratios": ["4:5", "3:2", "16:9"],
        "tone": "premium but realistic",
        "visual_priority": "architectural photography",
    },
}


@dataclass(frozen=True)
class ImagePromptContract:
    """Describe the request and response expectations for image prompts."""

    name: str
    required_request_fields: tuple[str, ...]
    required_response_fields: tuple[str, ...]
    supported_image_types: tuple[str, ...]
    supported_aspect_ratios: tuple[str, ...]
    supported_platforms: tuple[str, ...]
    defaults: dict[str, Any] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the contract."""

        return {
            "name": self.name,
            "required_request_fields": list(self.required_request_fields),
            "required_response_fields": list(self.required_response_fields),
            "supported_image_types": list(self.supported_image_types),
            "supported_aspect_ratios": list(self.supported_aspect_ratios),
            "supported_platforms": list(self.supported_platforms),
            "defaults": self.defaults,
            "aliases": self.aliases,
            "notes": self.notes,
        }


IMAGE_PROMPT_REQUEST_CONTRACT = ImagePromptContract(
    name="image_prompt_request",
    required_request_fields=("brand", "platform", "content_type", "image_type", "aspect_ratio", "creative_direction"),
    required_response_fields=("image_prompt", "style", "camera", "lighting", "negative_prompt"),
    supported_image_types=SUPPORTED_IMAGE_PROMPT_TYPES,
    supported_aspect_ratios=SUPPORTED_ASPECT_RATIOS,
    supported_platforms=SUPPORTED_PLATFORMS,
    defaults={
        "brand": "",
        "platform": "",
        "content_type": "image_prompt",
        "campaign_type": "",
        "objective": "",
        "audience": "",
        "location": "",
        "property_type": "",
        "visual_style": "",
        "creative_direction": "",
        "image_type": "social_media_visual",
        "aspect_ratio": "4:5",
        "extra_notes": "",
    },
    aliases={
        "image_prompt_type": "image_type",
        "visual_style": "visual_style",
        "aspect_ratio": "aspect_ratio",
        "raw": "creative_direction",
    },
    notes=[
        "Image prompts must remain concise, realistic, English-first, and platform-aware.",
    ],
)

IMAGE_PROMPT_RESPONSE_CONTRACT = ImagePromptContract(
    name="image_prompt_response",
    required_request_fields=IMAGE_PROMPT_REQUEST_CONTRACT.required_response_fields,
    required_response_fields=IMAGE_PROMPT_REQUEST_CONTRACT.required_response_fields,
    supported_image_types=SUPPORTED_IMAGE_PROMPT_TYPES,
    supported_aspect_ratios=SUPPORTED_ASPECT_RATIOS,
    supported_platforms=SUPPORTED_PLATFORMS,
    defaults={
        "success": True,
        "image_prompt": "",
        "style": "",
        "camera": "",
        "lighting": "",
        "negative_prompt": "",
        "prompt": "",
        "visual_style": "",
        "lighting_style": "",
        "composition_style": "",
        "camera_direction": "",
        "aspect_ratio": "4:5",
        "platform": "",
        "metadata": {},
        "warnings": [],
        "errors": [],
        "image_type": "",
        "cinematic_rules_applied": [],
        "validation": {},
    },
    notes=["Structured image prompt instructions only."],
)


def normalize_image_type(image_type: str) -> str:
    """Normalize image prompt type names."""

    return normalize_key(image_type)


def normalize_aspect_ratio(aspect_ratio: str) -> str:
    """Normalize aspect ratios while preserving colon-separated forms."""

    return str(aspect_ratio or "").strip()


def get_supported_image_prompt_types() -> list[str]:
    """Return supported image prompt types."""

    return list(SUPPORTED_IMAGE_PROMPT_TYPES)


def get_supported_aspect_ratios() -> list[str]:
    """Return supported aspect ratios."""

    return list(SUPPORTED_ASPECT_RATIOS)


def get_supported_platforms() -> list[str]:
    """Return supported platforms for image prompt guidance."""

    return list(SUPPORTED_PLATFORMS)


def build_image_prompt_request_contract() -> dict[str, Any]:
    """Return the request contract as a dictionary."""

    return IMAGE_PROMPT_REQUEST_CONTRACT.to_dict()


def build_image_prompt_response_contract() -> dict[str, Any]:
    """Return the response contract as a dictionary."""

    return IMAGE_PROMPT_RESPONSE_CONTRACT.to_dict()
