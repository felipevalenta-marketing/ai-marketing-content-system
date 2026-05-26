"""Context assembly helpers for prompt-ready AI knowledge blocks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.knowledge_loader import BrandKnowledge, load_brand_knowledge
from src.utils.logger import get_logger, log_context


@dataclass
class ContextBlock:
    """A reusable prompt-ready context block."""

    title: str
    body: str


class ContextBuilder:
    """Build layered AI context from brand markdown knowledge."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)

    def build_brand_context(self, bundle: BrandKnowledge) -> dict[str, Any]:
        """Return a structured view of the brand knowledge."""

        log_context(self.logger, f"Assembling brand context for {bundle.brand}")
        return {
            "brand": bundle.brand,
            "brand_root": bundle.brand_root,
            "brand_config": bundle.brand_config,
            "knowledge_base": bundle.knowledge_base,
            "raw_content": bundle.raw_content,
            "normalized_content": bundle.normalized_content,
            "metadata": bundle.metadata,
            "detected_categories": bundle.detected_categories,
            "warnings": bundle.warnings,
        }

    def build_combined_context(self, bundle: BrandKnowledge) -> str:
        """Build a long-form combined context string for prompt injection."""

        context = self.build_brand_context(bundle)
        blocks = [
            self.build_summary_block(context),
            self.build_tone_block(context),
            self.build_audience_block(context),
            self.build_market_block(context),
            self.build_lifestyle_block(context),
            self.build_visual_block(context),
        ]
        return "\n\n".join(block.body for block in blocks if block.body.strip())

    def build_storytelling_context(self, bundle: BrandKnowledge) -> str:
        """Build a combined storytelling context for campaigns and content systems."""

        return self.build_combined_context(bundle)

    def storytelling_context(self, bundle: BrandKnowledge) -> str:
        """Alias for storytelling-oriented prompt assembly."""

        return self.build_storytelling_context(bundle)

    def strategic_context(self, bundle: BrandKnowledge) -> str:
        """Build a compressed but high-priority context block."""

        layers = self.build_priority_layers(bundle)
        return (
            f"Brand config:\n{self._render_layer(layers['brand_config'])}\n\n"
            f"Buyer psychology:\n{self.get_buyer_psychology_context(bundle)}\n\n"
            f"Content rules:\n{self._render_layer(layers['content_rules'])}\n\n"
            f"Platform rules:\n{self._render_layer(layers['platform_rules'])}"
        )

    def condensed_context(self, bundle: BrandKnowledge, max_chars: int = 4000) -> str:
        """Return a compact context representation for token-aware prompts."""

        summary = self.build_summarized_context(bundle)
        text = (
            f"Brand: {summary['brand']}\n"
            f"Tone: {summary['tone']}\n"
            f"Audience: {summary['audience']}\n"
            f"Market: {summary['market']}\n"
            f"Lifestyle: {summary['lifestyle']}\n"
            f"Visual: {summary['visual']}\n"
            f"Buyer psychology: {summary['buyer_psychology']}"
        )
        return self._trim_text(text, max_chars)

    def build_priority_layers(
        self,
        bundle: BrandKnowledge,
        platform: str | None = None,
        property_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return layered context in priority order for future override systems."""

        layers = {
            "brand_config": bundle.brand_config,
            "content_rules": self._extract_path_text(bundle.brand_config, ["content_rules"]),
            "buyer_psychology": self._extract_path_text(bundle.knowledge_base, ["brand_story", "buyer_psychology"]),
            "platform_rules": self._extract_path_text(bundle.knowledge_base, ["content_examples", "platform_rules"]),
            "market": self.get_market_context(bundle),
            "neighborhoods": self._extract_path_text(bundle.knowledge_base, ["neighborhoods"]),
            "examples": self._extract_path_text(bundle.knowledge_base, ["content_examples"]),
            "property_specific": property_context or {},
        }
        if platform:
            layers["platform"] = platform.strip().lower()
        return layers

    def build_summary_block(self, context: dict[str, Any]) -> ContextBlock:
        """Create a top-level summary block."""

        return ContextBlock(
            title="Brand Summary",
            body=(
                f"Brand: {context['brand']}\n"
                f"Detected categories: {', '.join(context['detected_categories'])}"
            ),
        )

    def build_tone_block(self, context: dict[str, Any]) -> ContextBlock:
        """Create a tone-specific context block."""

        tone = self._extract_section_text(context.get("brand_config", {}), ["tone", "tone_md", "tone_of_voice"])
        return ContextBlock(title="Tone Context", body=self._format_block("Tone", tone))

    def build_audience_block(self, context: dict[str, Any]) -> ContextBlock:
        """Create an audience-specific context block."""

        audience = self._extract_section_text(context.get("brand_config", {}), ["audience"])
        return ContextBlock(title="Audience Context", body=self._format_block("Audience", audience))

    def build_market_block(self, context: dict[str, Any]) -> ContextBlock:
        """Create a market intelligence context block."""

        return ContextBlock(title="Market Context", body=self._format_block("Market", self._extract_path_text_from_context(context, ["market"])))

    def build_lifestyle_block(self, context: dict[str, Any]) -> ContextBlock:
        """Create a lifestyle and regional intelligence block."""

        knowledge_base = context.get("knowledge_base", {})
        lifestyle = self._combine_text(
            self._extract_path_text(knowledge_base, ["market", "east_mallorca_lifestyle"]),
            self._extract_path_text(knowledge_base, ["neighborhoods"]),
        )
        return ContextBlock(title="Lifestyle Context", body=self._format_block("Lifestyle", lifestyle))

    def build_visual_block(self, context: dict[str, Any]) -> ContextBlock:
        """Create a visual direction context block."""

        visual = self._extract_section_text(context.get("brand_config", {}), ["visual_identity"])
        return ContextBlock(title="Visual Context", body=self._format_block("Visual", visual))

    def build_summarized_context(self, bundle: BrandKnowledge) -> dict[str, Any]:
        """Return a compact summary suitable for lightweight prompts."""

        context = self.build_brand_context(bundle)
        return {
            "brand": context["brand"],
            "tone": self._extract_section_text(context.get("brand_config", {}), ["tone"])[:1200],
            "audience": self._extract_section_text(context.get("brand_config", {}), ["audience"])[:1200],
            "market": self.get_market_context(bundle)[:1200],
            "lifestyle": self._combine_text(
                self._extract_path_text(context.get("knowledge_base", {}), ["market"]),
                self._extract_path_text(context.get("knowledge_base", {}), ["neighborhoods"]),
            )[:1200],
            "visual": self.get_visual_identity_context(bundle)[:1200],
            "buyer_psychology": self.get_buyer_psychology_context(bundle)[:1200],
        }

    def build_platform_context(self, bundle: BrandKnowledge, platform: str) -> str:
        """Create platform-specific context text for prompt generation."""

        log_context(self.logger, f"Building platform context for {bundle.brand} on {platform}")
        summary = self.build_summarized_context(bundle)
        platform_rules = self.get_platform_context(bundle, platform)
        platform_name = platform.strip().lower()
        return (
            f"Platform: {platform_name}\n"
            f"Brand: {summary['brand']}\n"
            f"Tone: {summary['tone']}\n"
            f"Audience: {summary['audience']}\n"
            f"Market: {summary['market']}\n"
            f"Lifestyle: {summary['lifestyle']}\n"
            f"Platform Rules:\n{platform_rules or 'unavailable'}"
        )

    def build_image_generation_context(self, bundle: BrandKnowledge) -> str:
        """Create a visual prompt context block."""

        summary = self.build_summarized_context(bundle)
        return (
            f"Brand: {summary['brand']}\n"
            f"Visual direction: {summary['visual']}\n"
            f"Regional lifestyle: {summary['lifestyle']}\n"
            f"Buyer psychology: {summary['buyer_psychology']}"
        )

    def build_video_prompt_context(self, bundle: BrandKnowledge) -> str:
        """Create a video prompt context block."""

        summary = self.build_summarized_context(bundle)
        return (
            f"Brand: {summary['brand']}\n"
            f"Audience: {summary['audience']}\n"
            f"Lifestyle: {summary['lifestyle']}\n"
            f"Visual: {summary['visual']}\n"
            f"Platform Rules: {self.get_platform_context(bundle, 'video')}"
        )

    def build_instagram_context(self, bundle: BrandKnowledge) -> str:
        """Convenience wrapper for Instagram-specific prompts."""

        return self.build_platform_context(bundle, "instagram")

    def build_listing_context(self, bundle: BrandKnowledge) -> str:
        """Convenience wrapper for listing-generation prompts."""

        return self.build_platform_context(bundle, "listing")

    def build_video_context(self, bundle: BrandKnowledge) -> str:
        """Convenience wrapper for video-generation prompts."""

        return self.build_video_prompt_context(bundle)

    def visual_context(self, bundle: BrandKnowledge) -> str:
        """Return a focused visual direction context block."""

        return self.get_visual_identity_context(bundle)

    def get_market_context(self, bundle: BrandKnowledge) -> str:
        """Return the market intelligence context."""

        return self._extract_path_text(bundle.knowledge_base, ["market"])

    def get_neighborhood_context(self, bundle: BrandKnowledge, name: str) -> str:
        """Return a specific neighborhood context by filename key."""

        neighborhood = bundle.knowledge_base.get("neighborhoods", {}).get(name)
        return self._get_primary_text(neighborhood)

    def get_audience_context(self, bundle: BrandKnowledge, segment: str | None = None) -> str:
        """Return the audience context or a segment-specific excerpt."""

        audience = self._extract_path_text(bundle.brand_config, ["audience"])
        if not segment:
            return audience
        if segment.lower() in audience.lower():
            return audience
        return f"{segment}:\n{audience}"

    def get_visual_identity_context(self, bundle: BrandKnowledge) -> str:
        """Return the visual identity context."""

        return self._extract_path_text(bundle.brand_config, ["visual_identity"])

    def get_buyer_psychology_context(self, bundle: BrandKnowledge) -> str:
        """Return buyer psychology context."""

        return self._extract_path_text(bundle.knowledge_base, ["brand_story", "buyer_psychology"])

    def get_platform_context(self, bundle: BrandKnowledge, platform: str) -> str:
        """Return platform-specific guidance."""

        platform_name = platform.strip().lower()
        platform_rules = self._extract_path_text(bundle.knowledge_base, ["content_examples", "platform_rules"])
        uniqueness_rules = self._extract_path_text(bundle.knowledge_base, ["content_examples", "uniqueness_rules"])
        return (
            f"Platform: {platform_name}\n"
            f"{platform_rules}\n\n"
            f"Uniqueness Rules:\n{uniqueness_rules}"
        ).strip()

    def _extract_section_text(self, section: dict[str, Any], keys: list[str]) -> str:
        """Extract the first readable markdown block from a section."""

        for key in keys:
            text = self._get_primary_text(section.get(key))
            if text.strip():
                return text
        return ""

    def _extract_path_text(self, source: Any, path: list[str]) -> str:
        """Traverse a nested path and return the primary markdown text."""

        current = source
        for key in path:
            if not isinstance(current, dict):
                return ""
            current = current.get(key)
            if current is None:
                return ""
        return self._get_primary_text(current)

    def _extract_path_text_from_context(self, context: dict[str, Any], path: list[str]) -> str:
        """Extract text from the flattened brand context dictionary."""

        current: Any = context
        for key in path:
            if not isinstance(current, dict):
                return ""
            current = current.get(key)
            if current is None:
                return ""
        return self._get_primary_text(current)

    def _combine_text(self, *values: Any) -> str:
        """Combine multiple text fragments into a readable markdown block."""

        parts: list[str] = []
        for value in values:
            text = self._get_primary_text(value)
            if text.strip():
                parts.append(text)
        return "\n\n".join(parts)

    def _get_primary_text(self, value: Any) -> str:
        """Extract the most readable markdown text from a loaded node."""

        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            normalized = value.get("normalized_content")
            if isinstance(normalized, str) and normalized.strip():
                return normalized
            raw = value.get("content")
            if isinstance(raw, str) and raw.strip():
                return raw
            metadata = value.get("metadata")
            if isinstance(metadata, dict):
                for key in ("normalized_content", "raw_content"):
                    item = metadata.get(key)
                    if isinstance(item, str) and item.strip():
                        return item
            parts = [self._get_primary_text(item) for item in value.values()]
            return "\n\n".join(part for part in parts if part.strip())
        if isinstance(value, list):
            parts = [self._get_primary_text(item) for item in value]
            return "\n\n".join(part for part in parts if part.strip())
        return str(value)

    def _trim_text(self, text: str, max_chars: int) -> str:
        """Trim text for token-aware output without breaking the flow too aggressively."""

        if len(text) <= max_chars:
            return text
        return text[: max(0, max_chars - 3)].rstrip() + "..."

    def _render_layer(self, layer: Any) -> str:
        """Render a nested layer into readable markdown text."""

        return self._trim_text(self._get_primary_text(layer), 2500)

    def _format_block(self, title: str, text: str) -> str:
        """Format a prompt-ready block."""

        cleaned = text.strip()
        if not cleaned:
            return f"{title}: unavailable"
        return f"{title}:\n{cleaned}"


def build_brand_context(brand_name: str, brands_root: str | None = None) -> dict[str, Any]:
    """Load a brand and return structured context."""

    bundle = load_brand_knowledge(brand_name, brands_root=brands_root)
    return ContextBuilder().build_brand_context(bundle)


def build_storytelling_context(brand_name: str, brands_root: str | None = None) -> str:
    """Build a long-form storytelling context for a brand."""

    bundle = load_brand_knowledge(brand_name, brands_root=brands_root)
    return ContextBuilder().build_storytelling_context(bundle)


def build_instagram_context(brand_name: str, brands_root: str | None = None) -> str:
    """Build Instagram-ready context for a brand."""

    bundle = load_brand_knowledge(brand_name, brands_root=brands_root)
    return ContextBuilder().build_instagram_context(bundle)


def build_listing_context(brand_name: str, brands_root: str | None = None) -> str:
    """Build listing-generation context for a brand."""

    bundle = load_brand_knowledge(brand_name, brands_root=brands_root)
    return ContextBuilder().build_listing_context(bundle)


def build_video_prompt_context(brand_name: str, brands_root: str | None = None) -> str:
    """Build video-generation context for a brand."""

    bundle = load_brand_knowledge(brand_name, brands_root=brands_root)
    return ContextBuilder().build_video_prompt_context(bundle)
