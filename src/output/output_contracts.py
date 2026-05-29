"""Formal output contracts for normalized marketing assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


CONTENT_TYPE_ALIASES: dict[str, str] = {
    "linkedin_post": "instagram_post",
    "facebook_post": "instagram_post",
    "email_marketing": "campaign_asset",
    "seo_page": "campaign_asset",
    "ad_copy": "campaign_asset",
    "campaign_pack": "campaign_asset",
    "video_script": "video_script",
}


@dataclass(frozen=True)
class OutputContractSpec:
    """Describe the expected shape of a structured output."""

    content_type: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    field_types: dict[str, tuple[str, ...]]
    defaults: dict[str, Any] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the contract for orchestration and reporting."""

        return {
            "content_type": self.content_type,
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "field_types": {key: list(value) for key, value in self.field_types.items()},
            "defaults": self.defaults,
            "aliases": self.aliases,
            "notes": self.notes,
        }


CONTRACTS: dict[str, OutputContractSpec] = {
    "instagram_post": OutputContractSpec(
        content_type="instagram_post",
        required_fields=("hook", "caption", "cta", "hashtags"),
        optional_fields=("notes",),
        field_types={
            "hook": ("str",),
            "caption": ("str",),
            "cta": ("str", "none"),
            "hashtags": ("list",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"hook": "", "caption": "", "cta": "", "hashtags": [], "notes": "", "raw_content": ""},
        aliases={
            "call_to_action": "cta",
            "hashtags_list": "hashtags",
            "description": "caption",
            "summary": "caption",
            "raw": "raw_content",
        },
    ),
    "instagram_reel": OutputContractSpec(
        content_type="instagram_reel",
        required_fields=("hook", "script", "scene_direction", "cta", "hashtags"),
        optional_fields=("notes",),
        field_types={
            "hook": ("str",),
            "script": ("str",),
            "scene_direction": ("str",),
            "cta": ("str", "none"),
            "hashtags": ("list",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"hook": "", "script": "", "scene_direction": "", "cta": "", "hashtags": [], "notes": "", "raw_content": ""},
        aliases={
            "call_to_action": "cta",
            "hashtags_list": "hashtags",
            "scene": "scene_direction",
            "description": "script",
            "summary": "script",
            "raw": "raw_content",
        },
    ),
    "property_description": OutputContractSpec(
        content_type="property_description",
        required_fields=("title", "short_description", "long_description", "cta"),
        optional_fields=("highlights", "notes"),
        field_types={
            "title": ("str",),
            "short_description": ("str",),
            "long_description": ("str",),
            "highlights": ("list",),
            "cta": ("str", "none"),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={
            "title": "",
            "short_description": "",
            "long_description": "",
            "highlights": [],
            "cta": "",
            "notes": "",
            "raw_content": "",
        },
        aliases={
            "headline": "title",
            "summary": "short_description",
            "description": "long_description",
            "call_to_action": "cta",
            "features": "highlights",
            "raw": "raw_content",
        },
    ),
    "image_prompt": OutputContractSpec(
        content_type="image_prompt",
        required_fields=("visual_direction", "subject", "composition", "lighting", "style"),
        optional_fields=("negative_prompt", "notes"),
        field_types={
            "visual_direction": ("str",),
            "subject": ("str",),
            "composition": ("str",),
            "lighting": ("str",),
            "style": ("str",),
            "negative_prompt": ("str",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={
            "visual_direction": "",
            "subject": "",
            "composition": "",
            "lighting": "",
            "style": "",
            "negative_prompt": "",
            "notes": "",
            "raw_content": "",
        },
        aliases={
            "visual_style": "style",
            "visual": "visual_direction",
            "scene": "visual_direction",
            "raw": "raw_content",
        },
    ),
    "video_prompt": OutputContractSpec(
        content_type="video_prompt",
        required_fields=("scene_description", "camera_motion", "mood", "sequence"),
        optional_fields=("voiceover_direction", "notes"),
        field_types={
            "scene_description": ("str",),
            "camera_motion": ("str",),
            "mood": ("str",),
            "sequence": ("list",),
            "voiceover_direction": ("str",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={
            "scene_description": "",
            "camera_motion": "",
            "mood": "",
            "sequence": [],
            "voiceover_direction": "",
            "notes": "",
            "raw_content": "",
        },
        aliases={
            "scene": "scene_description",
            "motion": "camera_motion",
            "voiceover": "voiceover_direction",
            "raw": "raw_content",
        },
    ),
    "video_script": OutputContractSpec(
        content_type="video_script",
        required_fields=("hook", "script", "voiceover", "cta", "music_mood", "scene_sequence", "storyboard", "camera_direction"),
        optional_fields=("notes", "raw_content"),
        field_types={
            "hook": ("str",),
            "script": ("str",),
            "voiceover": ("str",),
            "cta": ("str", "none"),
            "music_mood": ("str",),
            "scene_sequence": ("list",),
            "storyboard": ("list",),
            "camera_direction": ("dict", "str"),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={
            "hook": "",
            "script": "",
            "voiceover": "",
            "cta": "",
            "music_mood": "",
            "scene_sequence": [],
            "storyboard": [],
            "camera_direction": {},
            "notes": "",
            "raw_content": "",
        },
        aliases={
            "scene": "scene_sequence",
            "scenes": "scene_sequence",
            "voiceover_direction": "voiceover",
            "call_to_action": "cta",
            "raw": "raw_content",
        },
    ),
    "campaign_asset": OutputContractSpec(
        content_type="campaign_asset",
        required_fields=("campaign_name", "objective", "main_message", "assets", "cta"),
        optional_fields=("notes",),
        field_types={
            "campaign_name": ("str",),
            "objective": ("str",),
            "main_message": ("str",),
            "assets": ("list",),
            "cta": ("str", "none"),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={
            "campaign_name": "",
            "objective": "",
            "main_message": "",
            "assets": [],
            "cta": "",
            "notes": "",
            "raw_content": "",
        },
        aliases={
            "name": "campaign_name",
            "message": "main_message",
            "resources": "assets",
            "call_to_action": "cta",
            "raw": "raw_content",
        },
    ),
}


def normalize_output_content_type(content_type: str) -> str:
    """Resolve content type aliases to canonical output contracts."""

    key = normalize_key(content_type)
    return CONTENT_TYPE_ALIASES.get(key, key)


def get_output_contract(content_type: str) -> OutputContractSpec:
    """Return the formal output contract for a content type."""

    key = normalize_output_content_type(content_type)
    contract = CONTRACTS.get(key)
    if contract is not None:
        return contract
    return CONTRACTS["campaign_asset"]


def list_supported_output_types() -> list[str]:
    """Return the registered canonical output content types."""

    return sorted(CONTRACTS.keys())
