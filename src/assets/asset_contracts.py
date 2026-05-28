"""Formal contracts for creative asset types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


ASSET_ALIASES: dict[str, str] = {
    "instagram_post": "social_post",
    "facebook_post": "social_post",
    "linkedin_post": "social_post",
    "text_caption": "text_caption",
    "social_post": "social_post",
    "instagram_reel": "reel_script",
    "video_script": "reel_script",
    "reel": "reel_script",
    "campaign_asset": "campaign_bundle",
    "campaign_pack": "campaign_bundle",
    "campaign_summary": "campaign_summary",
    "email_marketing": "email_teaser",
    "seo_page": "website_listing",
    "ad_copy": "social_post",
    "landing_page_copy": "website_listing",
    "blog_article": "website_listing",
    "generated_image": "image_prompt",
    "generated_video": "video_prompt",
}


@dataclass(frozen=True)
class AssetContract:
    """Describe the expected structure for a creative asset type."""

    asset_type: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    field_types: dict[str, tuple[str, ...]]
    defaults: dict[str, Any] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the asset contract."""

        return {
            "asset_type": self.asset_type,
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "field_types": {key: list(value) for key, value in self.field_types.items()},
            "defaults": self.defaults,
            "aliases": self.aliases,
            "notes": self.notes,
        }


ASSET_CONTRACTS: dict[str, AssetContract] = {
    "text_caption": AssetContract(
        asset_type="text_caption",
        required_fields=("platform", "hook", "caption", "cta", "hashtags", "governance_status"),
        optional_fields=("notes", "raw_content"),
        field_types={
            "platform": ("str",),
            "hook": ("str",),
            "caption": ("str",),
            "cta": ("str", "none"),
            "hashtags": ("list",),
            "governance_status": ("str",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"platform": "", "hook": "", "caption": "", "cta": "", "hashtags": [], "governance_status": "", "notes": "", "raw_content": ""},
        aliases={"call_to_action": "cta", "description": "caption", "summary": "caption", "raw": "raw_content"},
        notes=["Generic caption asset used across social and campaign workflows."],
    ),
    "social_post": AssetContract(
        asset_type="social_post",
        required_fields=("platform", "hook", "caption", "cta", "hashtags"),
        optional_fields=("notes", "raw_content"),
        field_types={
            "platform": ("str",),
            "hook": ("str",),
            "caption": ("str",),
            "cta": ("str", "none"),
            "hashtags": ("list",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"platform": "", "hook": "", "caption": "", "cta": "", "hashtags": [], "notes": "", "raw_content": ""},
        aliases={"call_to_action": "cta", "hashtags_list": "hashtags", "description": "caption", "summary": "caption", "raw": "raw_content"},
    ),
    "reel_script": AssetContract(
        asset_type="reel_script",
        required_fields=("hook", "script", "scenes", "voiceover_direction", "cta", "visual_direction"),
        optional_fields=("duration", "camera_direction", "music_mood", "storyboard", "notes", "raw_content"),
        field_types={
            "hook": ("str",),
            "script": ("str",),
            "scenes": ("list",),
            "voiceover_direction": ("str",),
            "cta": ("str", "none"),
            "visual_direction": ("str",),
            "duration": ("str",),
            "camera_direction": ("dict", "str"),
            "music_mood": ("str",),
            "storyboard": ("list",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"hook": "", "script": "", "scenes": [], "voiceover_direction": "", "cta": "", "visual_direction": "", "duration": "", "camera_direction": {}, "music_mood": "", "storyboard": [], "notes": "", "raw_content": ""},
        aliases={"scene": "scenes", "scene_sequence": "scenes", "description": "script", "summary": "script", "call_to_action": "cta", "camera": "camera_direction", "raw": "raw_content"},
    ),
    "property_description": AssetContract(
        asset_type="property_description",
        required_fields=("title", "short_description", "long_description", "highlights", "cta"),
        optional_fields=("notes", "raw_content"),
        field_types={
            "title": ("str",),
            "short_description": ("str",),
            "long_description": ("str",),
            "highlights": ("list",),
            "cta": ("str", "none"),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"title": "", "short_description": "", "long_description": "", "highlights": [], "cta": "", "notes": "", "raw_content": ""},
        aliases={"headline": "title", "summary": "short_description", "description": "long_description", "features": "highlights", "call_to_action": "cta", "raw": "raw_content"},
    ),
    "image_prompt": AssetContract(
        asset_type="image_prompt",
        required_fields=("subject", "composition", "lighting", "style", "aspect_ratio", "negative_prompt", "platform_use"),
        optional_fields=("notes", "raw_content"),
        field_types={
            "subject": ("str",),
            "composition": ("str",),
            "lighting": ("str",),
            "style": ("str",),
            "aspect_ratio": ("str",),
            "negative_prompt": ("str",),
            "platform_use": ("str",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"subject": "", "composition": "", "lighting": "", "style": "", "aspect_ratio": "", "negative_prompt": "", "platform_use": "", "notes": "", "raw_content": ""},
        aliases={"visual_style": "style", "raw": "raw_content"},
    ),
    "video_prompt": AssetContract(
        asset_type="video_prompt",
        required_fields=("scene_description", "camera_motion", "sequence", "mood", "duration", "voiceover_direction", "platform_use"),
        optional_fields=("storyboard", "camera_direction", "notes", "raw_content"),
        field_types={
            "scene_description": ("str",),
            "camera_motion": ("str",),
            "sequence": ("list",),
            "mood": ("str",),
            "duration": ("str",),
            "voiceover_direction": ("str",),
            "platform_use": ("str",),
            "storyboard": ("list",),
            "camera_direction": ("dict", "str"),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"scene_description": "", "camera_motion": "", "sequence": [], "mood": "", "duration": "", "voiceover_direction": "", "platform_use": "", "storyboard": [], "camera_direction": {}, "notes": "", "raw_content": ""},
        aliases={"scene": "scene_description", "motion": "camera_motion", "scene_sequence": "sequence", "raw": "raw_content"},
    ),
    "email_teaser": AssetContract(
        asset_type="email_teaser",
        required_fields=("subject", "preview_text", "body", "cta"),
        optional_fields=("notes", "raw_content"),
        field_types={
            "subject": ("str",),
            "preview_text": ("str",),
            "body": ("str",),
            "cta": ("str", "none"),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"subject": "", "preview_text": "", "body": "", "cta": "", "notes": "", "raw_content": ""},
        aliases={"summary": "preview_text", "description": "body", "call_to_action": "cta", "raw": "raw_content"},
    ),
    "website_listing": AssetContract(
        asset_type="website_listing",
        required_fields=("title", "short_description", "long_description", "highlights", "cta"),
        optional_fields=("notes", "raw_content"),
        field_types={
            "title": ("str",),
            "short_description": ("str",),
            "long_description": ("str",),
            "highlights": ("list",),
            "cta": ("str", "none"),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"title": "", "short_description": "", "long_description": "", "highlights": [], "cta": "", "notes": "", "raw_content": ""},
        aliases={"headline": "title", "summary": "short_description", "description": "long_description", "features": "highlights", "call_to_action": "cta", "raw": "raw_content"},
    ),
    "campaign_summary": AssetContract(
        asset_type="campaign_summary",
        required_fields=("campaign_name", "objective", "main_message", "assets"),
        optional_fields=("notes", "raw_content"),
        field_types={
            "campaign_name": ("str",),
            "objective": ("str",),
            "main_message": ("str",),
            "assets": ("list",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"campaign_name": "", "objective": "", "main_message": "", "assets": [], "notes": "", "raw_content": ""},
        aliases={"message": "main_message", "resources": "assets", "raw": "raw_content"},
    ),
    "campaign_bundle": AssetContract(
        asset_type="campaign_bundle",
        required_fields=("campaign_name", "assets", "platform_plan", "governance_summary"),
        optional_fields=("export_paths", "notes", "raw_content"),
        field_types={
            "campaign_name": ("str",),
            "assets": ("dict", "list"),
            "platform_plan": ("dict",),
            "governance_summary": ("dict",),
            "export_paths": ("dict",),
            "notes": ("str",),
            "raw_content": ("str",),
        },
        defaults={"campaign_name": "", "assets": {}, "platform_plan": {}, "governance_summary": {}, "export_paths": {}, "notes": "", "raw_content": ""},
        aliases={"bundle": "assets", "raw": "raw_content"},
    ),
}

for future_asset_type in (
    "carousel_outline",
    "story_sequence",
    "ad_creative",
    "landing_page_copy",
    "seo_page",
    "blog_article",
    "generated_image",
    "generated_video",
    "voiceover_script",
    "shot_list",
):
    ASSET_CONTRACTS.setdefault(
        future_asset_type,
        AssetContract(
            asset_type=future_asset_type,
            required_fields=("raw_content",),
            optional_fields=("notes",),
            field_types={"raw_content": ("str",), "notes": ("str",)},
            defaults={"raw_content": "", "notes": ""},
            aliases={"raw": "raw_content"},
            notes=["Future-ready asset contract placeholder."],
        ),
    )


def normalize_asset_type(asset_type: str) -> str:
    """Normalize asset type names to canonical contracts."""

    key = normalize_key(asset_type)
    return ASSET_ALIASES.get(key, key)


def get_asset_contract(asset_type: str) -> AssetContract:
    """Return the contract for an asset type."""

    key = normalize_asset_type(asset_type)
    contract = ASSET_CONTRACTS.get(key)
    if contract is not None:
        return contract
    return ASSET_CONTRACTS["campaign_bundle"]


def list_supported_asset_types() -> list[str]:
    """Return canonical asset types."""

    return sorted(ASSET_CONTRACTS.keys())
