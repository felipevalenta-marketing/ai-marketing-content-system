"""Platform behavior rules for prompt orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


@dataclass(frozen=True)
class PlatformRule:
    """Describe how a platform should shape output."""

    platform: str
    tone: str
    structure: str
    cta_style: str
    length: str
    storytelling_depth: str
    guidance: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""

        return {
            "platform": self.platform,
            "tone": self.tone,
            "structure": self.structure,
            "cta_style": self.cta_style,
            "length": self.length,
            "storytelling_depth": self.storytelling_depth,
            "guidance": self.guidance,
            "avoid": self.avoid,
        }


PLATFORM_RULES: dict[str, PlatformRule] = {
    "instagram": PlatformRule(
        platform="instagram",
        tone="emotional, visual, concise",
        structure="hook, value, proof, soft CTA",
        cta_style="short, elegant, lightly invitational",
        length="short to medium",
        storytelling_depth="moderate",
        guidance=[
            "lead with a strong visual hook",
            "favor lifestyle and emotion",
            "keep sentence rhythm polished and concise",
        ],
        avoid=[
            "long explanatory paragraphs",
            "heavy technical language",
            "overly promotional language",
        ],
    ),
    "facebook": PlatformRule(
        platform="facebook",
        tone="warm, accessible, informative",
        structure="context, value, reassurance, CTA",
        cta_style="clear and friendly",
        length="medium",
        storytelling_depth="moderate",
        guidance=[
            "add practical context",
            "support family and relocation audiences",
        ],
        avoid=[
            "overly terse copy",
            "abstract brand language without usefulness",
        ],
    ),
    "linkedin": PlatformRule(
        platform="linkedin",
        tone="professional, authority-driven, strategic",
        structure="insight, evidence, implication, CTA",
        cta_style="professional and direct",
        length="medium to long",
        storytelling_depth="high",
        guidance=[
            "sound informed and commercially credible",
            "prioritize market intelligence and positioning",
        ],
        avoid=[
            "social-only phrasing",
            "trend-led language",
        ],
    ),
    "seo": PlatformRule(
        platform="seo",
        tone="structured, keyword-aware, helpful",
        structure="heading-led, scannable, contextual",
        cta_style="informational and practical",
        length="long",
        storytelling_depth="high",
        guidance=[
            "use clear headings and topical depth",
            "include local context and search intent naturally",
        ],
        avoid=[
            "keyword stuffing",
            "generic destination copy",
        ],
    ),
    "video": PlatformRule(
        platform="video",
        tone="cinematic, descriptive, atmospheric",
        structure="scene, movement, detail, feeling",
        cta_style="soft and cinematic",
        length="medium",
        storytelling_depth="high",
        guidance=[
            "describe visuals in motion",
            "include atmosphere, pacing, and transitions",
        ],
        avoid=[
            "flat copy",
            "static descriptions without motion",
        ],
    ),
    "image": PlatformRule(
        platform="image",
        tone="visual, specific, art-directed",
        structure="subject, composition, lighting, mood",
        cta_style="n/a",
        length="short",
        storytelling_depth="low to medium",
        guidance=[
            "describe composition and realism clearly",
            "anchor prompts in place and texture",
        ],
        avoid=[
            "contradictory style directions",
            "overloaded prompt language",
        ],
    ),
    "email": PlatformRule(
        platform="email",
        tone="personal, premium, actionable",
        structure="subject, value, context, CTA",
        cta_style="clear and low-pressure",
        length="medium",
        storytelling_depth="moderate",
        guidance=[
            "keep the objective singular",
            "make the email feel human and easy to scan",
        ],
        avoid=[
            "long blocks of copy",
            "generic newsletter phrasing",
        ],
    ),
    "default": PlatformRule(
        platform="default",
        tone="adaptable",
        structure="clear and context-led",
        cta_style="context-appropriate",
        length="adaptive",
        storytelling_depth="adaptive",
        guidance=["match the platform and objective"],
        avoid=["one-size-fits-all writing"],
    ),
}


def get_platform_rule(platform: str) -> PlatformRule:
    """Return the rule set for a given platform."""

    key = normalize_key(platform)
    return PLATFORM_RULES.get(key, PLATFORM_RULES["default"])


def list_supported_platforms() -> list[str]:
    """Return supported platform names."""

    return sorted(platform for platform in PLATFORM_RULES if platform != "default")
