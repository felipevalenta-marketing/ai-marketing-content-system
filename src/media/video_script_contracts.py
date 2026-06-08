"""Serialization-safe contracts for video script and storyboard generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


SUPPORTED_VIDEO_TYPES = (
    "instagram_reel",
    "property_walkthrough",
    "lifestyle_video",
    "neighborhood_spotlight",
    "reform_opportunity_video",
    "relocation_video",
    "campaign_teaser",
    "listing_highlight",
    "brand_story_video",
    "youtube_short",
    "tiktok_video",
    "paid_ad_video",
    "website_hero_video",
    "cinematic_property_tour",
    "client_testimonial_script",
    "voiceover_ad",
)

SUPPORTED_DURATIONS = ("15s", "30s", "45s", "60s", "90s")

SUPPORTED_PLATFORMS = ("instagram", "tiktok", "facebook", "youtube", "website", "linkedin")

PLATFORM_VIDEO_GUIDANCE: dict[str, dict[str, Any]] = {
    "instagram": {
        "preferred_durations": ["15s", "30s", "45s"],
        "tone": "vertical-first, visual, lifestyle-driven, elegant",
    },
    "tiktok": {
        "preferred_durations": ["15s", "30s"],
        "tone": "fast hook, conversational, rhythm-first",
    },
    "facebook": {
        "preferred_durations": ["30s", "45s", "60s"],
        "tone": "warmer, clearer, community-oriented",
    },
    "youtube": {
        "preferred_durations": ["30s", "45s", "60s", "90s"],
        "tone": "polished, informative, viewer-retaining",
    },
    "website": {
        "preferred_durations": ["30s", "45s", "60s"],
        "tone": "factual, listing-ready, concise",
    },
    "linkedin": {
        "preferred_durations": ["30s", "45s", "60s"],
        "tone": "professional, strategic, authority-driven",
    },
}


@dataclass(frozen=True)
class VideoScriptContract:
    """Describe the request and response expectations for video scripts."""

    name: str
    required_request_fields: tuple[str, ...]
    required_response_fields: tuple[str, ...]
    supported_video_types: tuple[str, ...]
    supported_durations: tuple[str, ...]
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
            "supported_video_types": list(self.supported_video_types),
            "supported_durations": list(self.supported_durations),
            "supported_platforms": list(self.supported_platforms),
            "defaults": self.defaults,
            "aliases": self.aliases,
            "notes": self.notes,
        }


VIDEO_SCRIPT_REQUEST_CONTRACT = VideoScriptContract(
    name="video_script_request",
    required_request_fields=("brand", "platform", "content_type", "video_type", "duration", "creative_direction"),
    required_response_fields=("hook", "scene_1", "scene_2", "scene_3", "voiceover", "cta"),
    supported_video_types=SUPPORTED_VIDEO_TYPES,
    supported_durations=SUPPORTED_DURATIONS,
    supported_platforms=SUPPORTED_PLATFORMS,
    defaults={
        "brand": "",
        "platform": "",
        "content_type": "video_script",
        "campaign_type": "",
        "objective": "",
        "audience": "",
        "location": "",
        "property_type": "",
        "video_type": "instagram_reel",
        "duration": "30s",
        "creative_direction": "",
        "visual_style": "",
        "tone": "",
        "extra_notes": "",
    },
    aliases={
        "video_prompt_type": "video_type",
        "runtime": "duration",
        "raw": "creative_direction",
    },
    notes=[
        "Video scripts must remain concise, platform-ready, and production-friendly.",
    ],
)

VIDEO_SCRIPT_RESPONSE_CONTRACT = VideoScriptContract(
    name="video_script_response",
    required_request_fields=VIDEO_SCRIPT_REQUEST_CONTRACT.required_response_fields,
    required_response_fields=VIDEO_SCRIPT_REQUEST_CONTRACT.required_response_fields,
    supported_video_types=SUPPORTED_VIDEO_TYPES,
    supported_durations=SUPPORTED_DURATIONS,
    supported_platforms=SUPPORTED_PLATFORMS,
    defaults={
        "success": True,
        "video_type": "instagram_reel",
        "duration": "30s",
        "platform": "",
        "hook": "",
        "scene_1": "",
        "scene_2": "",
        "scene_3": "",
        "voiceover": "",
        "cta": "",
        "script": "",
        "music_mood": "",
        "scene_sequence": [],
        "storyboard": [],
        "camera_direction": {},
        "metadata": {},
        "warnings": [],
        "errors": [],
    },
    notes=["Structured video script and storyboard instructions only."],
)


def normalize_video_type(video_type: str) -> str:
    """Normalize video type names."""

    return normalize_key(video_type)


def normalize_duration(duration: str) -> str:
    """Normalize video durations while preserving the seconds suffix."""

    return str(duration or "").strip().lower().replace("seconds", "s")


def get_supported_video_types() -> list[str]:
    """Return supported video types."""

    return list(SUPPORTED_VIDEO_TYPES)


def get_supported_durations() -> list[str]:
    """Return supported durations."""

    return list(SUPPORTED_DURATIONS)


def get_supported_platforms() -> list[str]:
    """Return supported platforms for video scripts."""

    return list(SUPPORTED_PLATFORMS)


def build_video_script_request_contract() -> dict[str, Any]:
    """Return the request contract as a dictionary."""

    return VIDEO_SCRIPT_REQUEST_CONTRACT.to_dict()


def build_video_script_response_contract() -> dict[str, Any]:
    """Return the response contract as a dictionary."""

    return VIDEO_SCRIPT_RESPONSE_CONTRACT.to_dict()
