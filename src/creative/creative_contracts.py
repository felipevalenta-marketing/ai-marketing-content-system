"""Serialization-safe contracts for creative direction guidance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


SUPPORTED_CREATIVE_DIRECTION_TYPES = (
    "campaign_visual_direction",
    "property_launch_direction",
    "relocation_campaign_direction",
    "neighborhood_spotlight_direction",
    "reform_opportunity_direction",
    "lifestyle_campaign_direction",
    "luxury_listing_direction",
    "brand_awareness_direction",
    "paid_ads_direction",
    "landing_page_direction",
    "social_campaign_direction",
    "video_campaign_direction",
    "editorial_campaign_direction",
    "seasonal_campaign_direction",
)

SUPPORTED_PLATFORMS = ("instagram", "facebook", "linkedin", "email", "website")


@dataclass(frozen=True)
class CreativeDirectionContract:
    """Describe the request and response expectations for creative direction."""

    name: str
    required_request_fields: tuple[str, ...]
    required_response_fields: tuple[str, ...]
    supported_direction_types: tuple[str, ...]
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
            "supported_direction_types": list(self.supported_direction_types),
            "supported_platforms": list(self.supported_platforms),
            "defaults": self.defaults,
            "aliases": self.aliases,
            "notes": self.notes,
        }


CREATIVE_DIRECTION_REQUEST_CONTRACT = CreativeDirectionContract(
    name="creative_direction_request",
    required_request_fields=("brand", "campaign_type", "platform", "objective", "audience"),
    required_response_fields=("creative_direction_type", "visual_identity", "moodboard", "color_palette"),
    supported_direction_types=SUPPORTED_CREATIVE_DIRECTION_TYPES,
    supported_platforms=SUPPORTED_PLATFORMS,
    defaults={
        "brand": "",
        "campaign_type": "",
        "objective": "",
        "audience": "",
        "location": "",
        "property_type": "",
        "platforms": [],
        "visual_style": "",
        "tone": "",
        "creative_direction": "",
        "extra_notes": "",
        "creative_direction_type": "campaign_visual_direction",
    },
    aliases={
        "campaign_visual": "creative_direction_type",
        "visual_direction": "creative_direction",
        "style": "visual_style",
    },
    notes=["Creative direction should remain deterministic and brand-safe."],
)

CREATIVE_DIRECTION_RESPONSE_CONTRACT = CreativeDirectionContract(
    name="creative_direction_response",
    required_request_fields=CREATIVE_DIRECTION_REQUEST_CONTRACT.required_response_fields,
    required_response_fields=CREATIVE_DIRECTION_REQUEST_CONTRACT.required_response_fields,
    supported_direction_types=SUPPORTED_CREATIVE_DIRECTION_TYPES,
    supported_platforms=SUPPORTED_PLATFORMS,
    defaults={
        "success": True,
        "creative_direction_type": "campaign_visual_direction",
        "brand": "",
        "campaign_type": "",
        "visual_identity": {},
        "moodboard": {},
        "color_palette": {},
        "lighting_direction": "",
        "camera_style": "",
        "composition_rules": [],
        "platform_guidelines": {},
        "media_guidelines": {},
        "asset_guidelines": {},
        "governance_notes": [],
        "metadata": {},
        "warnings": [],
        "errors": [],
    },
    notes=["Structured creative direction guidance only."],
)


def normalize_creative_direction_type(value: str) -> str:
    """Normalize a creative direction type."""

    return normalize_key(value)


def get_supported_creative_direction_types() -> list[str]:
    """Return supported creative direction types."""

    return list(SUPPORTED_CREATIVE_DIRECTION_TYPES)


def get_supported_platforms() -> list[str]:
    """Return supported platforms."""

    return list(SUPPORTED_PLATFORMS)


def build_creative_direction_request_contract() -> dict[str, Any]:
    """Return the request contract as a dictionary."""

    return CREATIVE_DIRECTION_REQUEST_CONTRACT.to_dict()


def build_creative_direction_response_contract() -> dict[str, Any]:
    """Return the response contract as a dictionary."""

    return CREATIVE_DIRECTION_RESPONSE_CONTRACT.to_dict()
