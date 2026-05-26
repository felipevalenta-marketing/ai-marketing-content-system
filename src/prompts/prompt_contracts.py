"""Structured output contracts for prompt generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


@dataclass(frozen=True)
class OutputContract:
    """Define the expected structure of a generated prompt response."""

    content_type: str
    name: str
    fields: list[str]
    description: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the contract."""

        return {
            "content_type": self.content_type,
            "name": self.name,
            "fields": self.fields,
            "description": self.description,
            "notes": self.notes,
        }

    def to_instruction_block(self) -> str:
        """Render the contract as output instructions."""

        lines = [f"Expected output: {self.name}"]
        lines.extend(f"- {field}" for field in self.fields)
        if self.notes:
            lines.append("Notes:")
            lines.extend(f"- {note}" for note in self.notes)
        return "\n".join(lines)


OUTPUT_CONTRACTS: dict[str, OutputContract] = {
    "instagram_post": OutputContract(
        content_type="instagram_post",
        name="instagram_post_contract",
        fields=["hook", "caption", "hashtags", "cta"],
        description="Standard social output for Instagram posts.",
        notes=["Keep the hook concise and the CTA soft."],
    ),
    "instagram_reel": OutputContract(
        content_type="instagram_reel",
        name="instagram_reel_contract",
        fields=["hook", "caption", "hashtags", "cta"],
        description="Standard social output for Instagram reels.",
        notes=["Support motion, mood, and visual pacing."],
    ),
    "facebook_post": OutputContract(
        content_type="facebook_post",
        name="facebook_post_contract",
        fields=["hook", "caption", "cta"],
        description="Facebook-friendly post structure.",
    ),
    "linkedin_post": OutputContract(
        content_type="linkedin_post",
        name="linkedin_post_contract",
        fields=["hook", "insight", "cta"],
        description="Professional thought-leadership structure.",
    ),
    "property_description": OutputContract(
        content_type="property_description",
        name="property_description_contract",
        fields=["headline", "description", "highlights", "cta"],
        description="Listing description output.",
    ),
    "neighborhood_story": OutputContract(
        content_type="neighborhood_story",
        name="neighborhood_story_contract",
        fields=["headline", "story", "seo_themes", "cta"],
        description="Area story output for SEO and lifestyle content.",
    ),
    "relocation_content": OutputContract(
        content_type="relocation_content",
        name="relocation_content_contract",
        fields=["headline", "guidance", "practical_points", "cta"],
        description="Relocation-focused informational output.",
    ),
    "email_marketing": OutputContract(
        content_type="email_marketing",
        name="email_marketing_contract",
        fields=["subject_line", "preview_text", "body", "cta"],
        description="Email marketing output.",
    ),
    "seo_page": OutputContract(
        content_type="seo_page",
        name="seo_page_contract",
        fields=["title", "meta_description", "outline", "body", "cta"],
        description="SEO page structure.",
    ),
    "image_prompt": OutputContract(
        content_type="image_prompt",
        name="image_prompt_contract",
        fields=["visual_direction", "lighting", "composition", "camera_style"],
        description="Image generation prompt output.",
    ),
    "video_prompt": OutputContract(
        content_type="video_prompt",
        name="video_prompt_contract",
        fields=["scene_description", "camera_motion", "mood", "voiceover_direction"],
        description="Video generation prompt output.",
    ),
    "ad_copy": OutputContract(
        content_type="ad_copy",
        name="ad_copy_contract",
        fields=["hook", "body_copy", "cta"],
        description="Short-form ad copy structure.",
    ),
    "campaign_pack": OutputContract(
        content_type="campaign_pack",
        name="campaign_pack_contract",
        fields=["campaign_angle", "hook_variations", "caption_variations", "cta_options", "asset_notes"],
        description="Multi-asset campaign planning output.",
    ),
}


def get_output_contract(content_type: str) -> OutputContract:
    """Return the output contract for a content type."""

    key = normalize_key(content_type)
    return OUTPUT_CONTRACTS.get(key, OutputContract(key or "unknown", "generic_contract", ["summary"], notes=["Fallback contract."]))


def build_output_instructions(content_type: str) -> str:
    """Return prompt instructions describing the expected output shape."""

    return get_output_contract(content_type).to_instruction_block()


def list_output_contracts() -> dict[str, dict[str, Any]]:
    """Return all output contracts."""

    return {key: contract.to_dict() for key, contract in OUTPUT_CONTRACTS.items()}
