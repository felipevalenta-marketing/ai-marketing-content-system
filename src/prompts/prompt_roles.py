"""Role-based prompt strategy definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


@dataclass(frozen=True)
class PromptRole:
    """Describe a specialized AI role for prompt orchestration."""

    name: str
    tone: str
    vocabulary: list[str] = field(default_factory=list)
    storytelling: str = ""
    structure: str = ""
    cta_behavior: str = ""
    guidance: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the role strategy."""

        return {
            "name": self.name,
            "tone": self.tone,
            "vocabulary": self.vocabulary,
            "storytelling": self.storytelling,
            "structure": self.structure,
            "cta_behavior": self.cta_behavior,
            "guidance": self.guidance,
            "avoid": self.avoid,
        }


ROLE_LIBRARY: dict[str, PromptRole] = {
    "luxury_copywriter": PromptRole(
        name="luxury_copywriter",
        tone="premium, polished, confident",
        vocabulary=["refined", "curated", "elevated", "timeless", "considered"],
        storytelling="focus on elegance, service, and value",
        structure="hook, value, proof, soft CTA",
        cta_behavior="low-pressure and discreet",
        guidance=[
            "use precise descriptive language",
            "balance luxury with credibility",
        ],
        avoid=["hype", "generic exclusivity", "empty superlatives"],
    ),
    "relocation_specialist": PromptRole(
        name="relocation_specialist",
        tone="supportive, practical, reassuring",
        vocabulary=["connected", "practical", "family-friendly", "livable", "informed"],
        storytelling="focus on transition, fit, and everyday ease",
        structure="context, reassurance, practical value, CTA",
        cta_behavior="helpful and welcoming",
        guidance=[
            "reduce uncertainty",
            "explain the benefits of place and routine",
        ],
        avoid=["aspirational fluff", "overpromising", "sales pressure"],
    ),
    "real_estate_marketer": PromptRole(
        name="real_estate_marketer",
        tone="strategic, clear, market-aware",
        vocabulary=["positioning", "market", "demand", "visibility", "value"],
        storytelling="focus on audience fit and property relevance",
        structure="insight, positioning, proof, CTA",
        cta_behavior="direct but refined",
        guidance=["highlight the right buyer fit", "keep the message commercially clear"],
        avoid=["generic property language", "unsupported claims"],
    ),
    "seo_specialist": PromptRole(
        name="seo_specialist",
        tone="structured, informative, keyword-aware",
        vocabulary=["guide", "area", "property", "market", "search intent"],
        storytelling="focus on discoverability and useful local depth",
        structure="heading-led, scannable, contextual",
        cta_behavior="informational",
        guidance=["use search-friendly structure", "keep readability high"],
        avoid=["keyword stuffing", "thin content"],
    ),
    "cinematic_director": PromptRole(
        name="cinematic_director",
        tone="cinematic, atmospheric, visual",
        vocabulary=["scene", "motion", "light", "texture", "framing"],
        storytelling="sequence the experience through movement and mood",
        structure="scene, motion, detail, feeling",
        cta_behavior="soft cinematic invitation",
        guidance=["think in sequences and transitions", "describe movement and atmosphere"],
        avoid=["flat staging", "static description"],
    ),
    "visual_storyteller": PromptRole(
        name="visual_storyteller",
        tone="art-directed, evocative, precise",
        vocabulary=["composition", "palette", "lens", "texture", "atmosphere"],
        storytelling="translate brand and place into visual cues",
        structure="subject, composition, lighting, mood",
        cta_behavior="n/a",
        guidance=["be specific about visual elements", "keep realism believable"],
        avoid=["contradictory instructions", "overloaded prompts"],
    ),
    "campaign_strategist": PromptRole(
        name="campaign_strategist",
        tone="planned, coordinated, performance-aware",
        vocabulary=["campaign", "sequence", "conversion", "variation", "funnel"],
        storytelling="connect multiple assets into one strategy",
        structure="objective, angle, asset, CTA",
        cta_behavior="varied by funnel stage",
        guidance=["optimize for multi-asset consistency", "support sequential prompts"],
        avoid=["fragmented messaging", "one-off thinking"],
    ),
    "default": PromptRole(
        name="default",
        tone="adaptable",
        vocabulary=["clear", "relevant", "purposeful"],
        storytelling="match the request and audience",
        structure="clear and context-led",
        cta_behavior="context-appropriate",
        guidance=["adapt to the brief"],
        avoid=["one-size-fits-all writing"],
    ),
}


CONTENT_TYPE_ROLE_MAP: dict[str, str] = {
    "instagram_post": "luxury_copywriter",
    "instagram_reel": "visual_storyteller",
    "facebook_post": "real_estate_marketer",
    "linkedin_post": "real_estate_marketer",
    "property_description": "luxury_copywriter",
    "neighborhood_story": "real_estate_marketer",
    "relocation_content": "relocation_specialist",
    "email_marketing": "campaign_strategist",
    "seo_page": "seo_specialist",
    "image_prompt": "visual_storyteller",
    "video_prompt": "cinematic_director",
    "video_script": "cinematic_director",
    "ad_copy": "campaign_strategist",
    "campaign_pack": "campaign_strategist",
}


def get_role(role_name: str | None, content_type: str | None = None) -> PromptRole:
    """Resolve a role by explicit name or content type."""

    if role_name:
        key = normalize_key(role_name)
        if key in ROLE_LIBRARY:
            return ROLE_LIBRARY[key]
    if content_type:
        key = normalize_key(content_type)
        role_key = CONTENT_TYPE_ROLE_MAP.get(key, "default")
        return ROLE_LIBRARY[role_key]
    return ROLE_LIBRARY["default"]


def list_supported_roles() -> list[str]:
    """Return supported role names."""

    return sorted(role for role in ROLE_LIBRARY if role != "default")
