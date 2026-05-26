"""Semantic registry for markdown knowledge and AI context routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import fnmatch


@dataclass(frozen=True)
class ContextRegistryEntry:
    """Semantic metadata for a markdown knowledge file."""

    role: str
    priority: str
    usage: list[str] = field(default_factory=list)


class ContextRegistry:
    """Resolve semantic roles and priorities for markdown knowledge files."""

    def __init__(self) -> None:
        self._entries: list[tuple[str, ContextRegistryEntry]] = [
            ("brand_config/tone.md", ContextRegistryEntry("strategic_brand_voice", "high", ["copywriting", "captions", "campaigns"])),
            ("brand_config/audience.md", ContextRegistryEntry("audience_strategy", "high", ["copywriting", "campaigns", "segmentation"])),
            ("brand_config/positioning.md", ContextRegistryEntry("brand_positioning", "high", ["copywriting", "strategy", "campaigns"])),
            ("brand_config/visual_identity.md", ContextRegistryEntry("visual_identity_system", "high", ["image_generation", "video_generation", "campaigns"])),
            ("brand_config/content_rules.md", ContextRegistryEntry("content_governance", "high", ["copywriting", "prompting", "qa"])),
            ("brand_story/buyer_psychology.md", ContextRegistryEntry("emotional_storytelling", "high", ["ads", "reels", "lifestyle_content"])),
            ("content_examples/platform_rules.md", ContextRegistryEntry("platform_orchestration", "high", ["copywriting", "platform_strategy", "content_generation"])),
            ("content_examples/uniqueness_rules.md", ContextRegistryEntry("anti_repetition_system", "high", ["copywriting", "quality_control", "campaigns"])),
            ("market/east_mallorca_lifestyle.md", ContextRegistryEntry("regional_lifestyle_strategy", "high", ["relocation", "seo", "lifestyle_content"])),
            ("market/market_personas.md", ContextRegistryEntry("market_persona_model", "high", ["segmentation", "copywriting", "campaigns"])),
            ("market/*.md", ContextRegistryEntry("market_intelligence", "medium", ["market_commentary", "seo", "campaigns"])),
            ("neighborhoods/*.md", ContextRegistryEntry("regional_storytelling", "medium", ["location_copy", "seo", "lifestyle_content"])),
            ("properties/*.md", ContextRegistryEntry("property_intelligence", "medium", ["listing_copy", "image_generation", "campaigns"])),
            ("services/*.md", ContextRegistryEntry("service_intelligence", "medium", ["copywriting", "sales_support", "about_pages"])),
            ("competitors/*.md", ContextRegistryEntry("competitive_intelligence", "medium", ["positioning", "sales_support", "strategy"])),
            ("content_examples/*.md", ContextRegistryEntry("content_operations", "medium", ["platform_strategy", "copywriting", "prompting"])),
        ]

    def resolve(self, relative_path: str | Path) -> ContextRegistryEntry:
        """Resolve semantic metadata for a file by its relative path."""

        normalized = str(relative_path).replace("\\", "/").lower()
        for pattern, entry in self._entries:
            if fnmatch.fnmatch(normalized, pattern.lower()):
                return entry
        return ContextRegistryEntry("general_knowledge", "low", ["prompting", "reference"])
