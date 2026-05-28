"""Platform-specific adaptation constraints and guardrails."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.adapters.platform_contracts import get_platform_contract, list_supported_platforms, normalize_platform_name


@dataclass(frozen=True)
class PlatformConstraints:
    """Describe how a platform should be adapted."""

    platform: str
    tone: str
    length: str
    hashtag_policy: str
    cta_style: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize platform constraints."""

        return {
            "platform": self.platform,
            "tone": self.tone,
            "length": self.length,
            "hashtag_policy": self.hashtag_policy,
            "cta_style": self.cta_style,
            "notes": self.notes,
        }


PLATFORM_CONSTRAINTS: dict[str, PlatformConstraints] = {
    "instagram": PlatformConstraints(
        platform="instagram",
        tone="lifestyle_emotional",
        length="short",
        hashtag_policy="allowed",
        cta_style="elegant_direct",
        notes=["Strong hook, short paragraphs, visually led copy."],
    ),
    "facebook": PlatformConstraints(
        platform="facebook",
        tone="warm_community",
        length="medium",
        hashtag_policy="limited",
        cta_style="soft_direct",
        notes=["Warmer community framing with slightly longer explanation."],
    ),
    "linkedin": PlatformConstraints(
        platform="linkedin",
        tone="professional_authority",
        length="medium",
        hashtag_policy="minimal",
        cta_style="authority_driven",
        notes=["Market insight over emotion, no overly promotional language."],
    ),
    "email": PlatformConstraints(
        platform="email",
        tone="clear_direct",
        length="medium",
        hashtag_policy="none",
        cta_style="direct",
        notes=["Subject, preview text, and body must remain clean and readable."],
    ),
    "website_listing": PlatformConstraints(
        platform="website_listing",
        tone="factual_informative",
        length="long",
        hashtag_policy="none",
        cta_style="informative",
        notes=["Informative and factual, with strong long-form clarity."],
    ),
}


def get_platform_constraints(platform: str) -> PlatformConstraints:
    """Return the constraints for a platform."""

    key = normalize_platform_name(platform)
    return PLATFORM_CONSTRAINTS.get(key, PLATFORM_CONSTRAINTS["instagram"])
