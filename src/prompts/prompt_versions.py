"""Prompt version registry for iterative prompt engineering."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.utils.file_utils import normalize_key


@dataclass(frozen=True)
class PromptVersion:
    """Describe a versioned prompt family."""

    version: str
    content_type: str
    platform: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the version record."""

        return {
            "version": self.version,
            "content_type": self.content_type,
            "platform": self.platform,
            "notes": self.notes,
        }


VERSION_LIBRARY: dict[str, PromptVersion] = {
    "instagram_post": PromptVersion("INSTAGRAM_POST_V1", "instagram_post", "instagram", "Baseline Instagram post prompt."),
    "instagram_reel": PromptVersion("INSTAGRAM_REEL_V2", "instagram_reel", "instagram", "Reel prompt tuned for motion and hooks."),
    "facebook_post": PromptVersion("FACEBOOK_POST_V1", "facebook_post", "facebook", "Baseline Facebook post prompt."),
    "linkedin_post": PromptVersion("LINKEDIN_POST_V1", "linkedin_post", "linkedin", "Authority-led professional prompt."),
    "property_description": PromptVersion("PROPERTY_DESCRIPTION_V1", "property_description", "listing", "Listing description prompt."),
    "neighborhood_story": PromptVersion("NEIGHBORHOOD_STORY_V1", "neighborhood_story", "seo", "Neighborhood storytelling prompt."),
    "relocation_content": PromptVersion("RELOCATION_CONTENT_V1", "relocation_content", "seo", "Relocation content prompt."),
    "email_marketing": PromptVersion("EMAIL_MARKETING_V1", "email_marketing", "email", "Email campaign prompt."),
    "seo_page": PromptVersion("SEO_PAGE_V1", "seo_page", "seo", "SEO page prompt."),
    "image_prompt": PromptVersion("IMAGE_PROMPT_V3", "image_prompt", "image", "Image prompt tuned for visual specificity."),
    "video_prompt": PromptVersion("VIDEO_PROMPT_V2", "video_prompt", "video", "Video prompt tuned for cinematic sequencing."),
    "video_script": PromptVersion("VIDEO_SCRIPT_V1", "video_script", "video", "Short-form video script and storyboard prompt."),
    "ad_copy": PromptVersion("AD_COPY_V1", "ad_copy", "social", "Paid social copy prompt."),
    "campaign_pack": PromptVersion("CAMPAIGN_PACK_V1", "campaign_pack", "campaign", "Multi-asset campaign prompt."),
}


def resolve_prompt_version(content_type: str, platform: str | None = None) -> PromptVersion:
    """Resolve a prompt version for a given content type and platform."""

    key = normalize_key(content_type)
    version = VERSION_LIBRARY.get(key)
    if version:
        return version

    platform_key = normalize_key(platform or "campaign")
    return PromptVersion(
        version=f"{platform_key.upper()}_V1",
        content_type=key or "unknown",
        platform=platform_key,
        notes="Fallback version generated for unsupported content types.",
    )


def list_prompt_versions() -> dict[str, dict[str, Any]]:
    """Return the full version registry."""

    return {key: value.to_dict() for key, value in VERSION_LIBRARY.items()}
