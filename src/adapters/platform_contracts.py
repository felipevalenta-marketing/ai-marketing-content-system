"""Platform output contracts for deterministic content adaptation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


PLATFORM_ALIASES: dict[str, str] = {
    "tiktok": "instagram",
    "youtube_shorts": "instagram",
    "blog": "website_listing",
    "seo_page": "website_listing",
    "ads": "facebook",
}


@dataclass(frozen=True)
class PlatformContract:
    """Describe a platform-specific output structure."""

    platform: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...]
    field_types: dict[str, tuple[str, ...]]
    defaults: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the contract."""

        return {
            "platform": self.platform,
            "required_fields": list(self.required_fields),
            "optional_fields": list(self.optional_fields),
            "field_types": {key: list(value) for key, value in self.field_types.items()},
            "defaults": self.defaults,
            "notes": self.notes,
        }


PLATFORM_CONTRACTS: dict[str, PlatformContract] = {
    "instagram": PlatformContract(
        platform="instagram",
        required_fields=("hook", "caption", "cta", "hashtags"),
        optional_fields=(),
        field_types={"hook": ("str",), "caption": ("str",), "cta": ("str",), "hashtags": ("list",)},
        defaults={"hook": "", "caption": "", "cta": "", "hashtags": []},
        notes=["Strong hook, visual caption, concise paragraphs, hashtags allowed."],
    ),
    "facebook": PlatformContract(
        platform="facebook",
        required_fields=("post", "cta", "hashtags"),
        optional_fields=(),
        field_types={"post": ("str",), "cta": ("str",), "hashtags": ("list",)},
        defaults={"post": "", "cta": "", "hashtags": []},
        notes=["Warmer tone, community-oriented, slightly longer explanation."],
    ),
    "linkedin": PlatformContract(
        platform="linkedin",
        required_fields=("headline", "body", "cta", "hashtags"),
        optional_fields=(),
        field_types={"headline": ("str",), "body": ("str",), "cta": ("str",), "hashtags": ("list",)},
        defaults={"headline": "", "body": "", "cta": "", "hashtags": []},
        notes=["Professional tone, strategic angle, minimal hashtags."],
    ),
    "email": PlatformContract(
        platform="email",
        required_fields=("subject", "preview_text", "body", "cta"),
        optional_fields=(),
        field_types={"subject": ("str",), "preview_text": ("str",), "body": ("str",), "cta": ("str",)},
        defaults={"subject": "", "preview_text": "", "body": "", "cta": ""},
        notes=["Subject line, preview text, direct CTA, no hashtags."],
    ),
    "website_listing": PlatformContract(
        platform="website_listing",
        required_fields=("title", "short_description", "long_description", "highlights", "cta"),
        optional_fields=(),
        field_types={
            "title": ("str",),
            "short_description": ("str",),
            "long_description": ("str",),
            "highlights": ("list",),
            "cta": ("str",),
        },
        defaults={"title": "", "short_description": "", "long_description": "", "highlights": [], "cta": ""},
        notes=["Factual title, informative tone, no hashtags."],
    ),
}


def normalize_platform_name(platform: str) -> str:
    """Normalize a platform name and resolve aliases."""

    key = normalize_key(platform)
    return PLATFORM_ALIASES.get(key, key)


def get_platform_contract(platform: str) -> PlatformContract:
    """Return the platform contract for a platform."""

    key = normalize_platform_name(platform)
    return PLATFORM_CONTRACTS.get(key, PLATFORM_CONTRACTS["instagram"])


def list_supported_platforms() -> list[str]:
    """Return canonical supported platform names."""

    return sorted(PLATFORM_CONTRACTS.keys())
