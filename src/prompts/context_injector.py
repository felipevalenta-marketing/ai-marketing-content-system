"""Selective prompt context injection for brand-aware generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.core.context_builder import ContextBuilder
from src.core.knowledge_loader import BrandKnowledge
from src.prompts.platform_rules import get_platform_rule
from src.prompts.prompt_roles import PromptRole, get_role
from src.prompts.prompt_versions import PromptVersion, resolve_prompt_version
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context


@dataclass(frozen=True)
class PromptRequest:
    """Structured prompt input used by the orchestration layer."""

    brand: str
    platform: str
    content_type: str
    objective: str
    prompt: str | None = None
    audience: str | None = None
    location: str | None = None
    property_type: str | None = None
    keyword_theme: str | None = None
    role: str | None = None
    prompt_version: str | None = None
    chain_step: str | None = None
    extra_context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InjectedContext:
    """A token-aware context bundle assembled for prompt generation."""

    brand: str
    platform: str
    content_type: str
    objective: str
    role_strategy: str
    prompt_version: str
    sections: dict[str, str]
    context_used: list[str]
    platform_rules: list[str]
    injected_categories: list[str]
    token_estimate: int
    empty_sections: list[str]
    source_preview: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the injected context."""

        return {
            "brand": self.brand,
            "platform": self.platform,
            "content_type": self.content_type,
            "objective": self.objective,
            "role_strategy": self.role_strategy,
            "prompt_version": self.prompt_version,
            "sections": self.sections,
            "context_used": self.context_used,
            "platform_rules": self.platform_rules,
            "injected_categories": self.injected_categories,
            "token_estimate": self.token_estimate,
            "empty_sections": self.empty_sections,
            "source_preview": self.source_preview,
        }


CONTENT_CONTEXT_MAP: dict[str, list[str]] = {
    "instagram_post": ["tone", "audience", "positioning", "buyer_psychology", "platform_rules", "neighborhood"],
    "instagram_reel": ["tone", "audience", "positioning", "buyer_psychology", "platform_rules", "visual", "neighborhood"],
    "facebook_post": ["tone", "audience", "market", "platform_rules", "neighborhood"],
    "linkedin_post": ["tone", "positioning", "audience", "market", "content_rules", "platform_rules"],
    "property_description": ["tone", "positioning", "content_rules", "market", "neighborhood", "audience"],
    "neighborhood_story": ["tone", "positioning", "market", "neighborhood", "buyer_psychology", "content_rules"],
    "relocation_content": ["tone", "audience", "buyer_psychology", "market", "neighborhood", "content_rules"],
    "email_marketing": ["tone", "audience", "positioning", "buyer_psychology", "platform_rules", "content_rules"],
    "seo_page": ["positioning", "market", "neighborhood", "content_rules", "audience"],
    "image_prompt": ["visual", "positioning", "market", "neighborhood", "buyer_psychology"],
    "video_prompt": ["visual", "tone", "audience", "market", "neighborhood", "platform_rules"],
    "video_script": ["visual", "tone", "audience", "market", "neighborhood", "platform_rules"],
    "ad_copy": ["tone", "audience", "buyer_psychology", "positioning", "platform_rules"],
    "campaign_pack": ["tone", "audience", "positioning", "buyer_psychology", "market", "neighborhood", "platform_rules", "content_rules", "examples"],
}

DEFAULT_CONTEXT_SEQUENCE = CONTENT_CONTEXT_MAP["campaign_pack"]
COMPACT_CONTEXT_TYPES = {
    "linkedin_post",
    "facebook_post",
    "ad_copy",
    "property_description",
    "image_prompt",
    "video_script",
    "instagram_reel",
}
COMPACT_CONTEXT_CHAR_LIMIT = 1500


SECTION_PRIORITY = {
    "brand_config": 0,
    "content_rules": 1,
    "buyer_psychology": 2,
    "platform_rules": 3,
    "market": 4,
    "neighborhood": 5,
    "examples": 6,
    "visual": 7,
}


class ContextInjector:
    """Select and compress brand context for prompt assembly."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.builder = ContextBuilder(logger=self.logger)

    def inject(
        self,
        bundle: BrandKnowledge,
        request: PromptRequest,
        token_budget: int | None = None,
        compact: bool = False,
    ) -> InjectedContext:
        """Build a selective context package for the requested prompt."""

        log_context(self.logger, f"Injecting context for {request.brand}/{request.platform}/{request.content_type}")
        content_type_key = normalize_key(request.content_type)
        compact_mode = compact or content_type_key in COMPACT_CONTEXT_TYPES
        role = get_role(request.role, request.content_type)
        version = resolve_prompt_version(request.content_type, request.platform)
        selected_sections = self._select_sections(bundle, request, content_type_key, role, version, compact_mode=compact_mode)
        ordered_sections = self._apply_token_budget(selected_sections, token_budget)
        if compact_mode:
            char_limit = min(token_budget or COMPACT_CONTEXT_CHAR_LIMIT, COMPACT_CONTEXT_CHAR_LIMIT)
            ordered_sections = self._cap_sections_to_chars(ordered_sections, char_limit)

        sections = {section["name"]: section["text"] for section in ordered_sections}
        context_used = [section["source"] for section in ordered_sections]
        platform_rule = get_platform_rule(request.platform)
        platform_rules = [platform_rule.platform, *platform_rule.guidance]
        injected_categories = [section["name"] for section in ordered_sections]
        empty_sections = [section["name"] for section in selected_sections if not section["text"].strip()]
        token_estimate = sum(section["chars"] for section in ordered_sections)
        source_preview = {section["name"]: section["text"][:220] for section in ordered_sections}

        return InjectedContext(
            brand=request.brand,
            platform=request.platform,
            content_type=request.content_type,
            objective=request.objective,
            role_strategy=role.name,
            prompt_version=request.prompt_version or version.version,
            sections=sections,
            context_used=context_used,
            platform_rules=platform_rules,
            injected_categories=injected_categories,
            token_estimate=token_estimate,
            empty_sections=empty_sections,
            source_preview=source_preview,
        )

    def _select_sections(
        self,
        bundle: BrandKnowledge,
        request: PromptRequest,
        content_type_key: str,
        role: PromptRole,
        version: PromptVersion,
        *,
        compact_mode: bool = False,
    ) -> list[dict[str, Any]]:
        """Select the sections relevant to the prompt request."""

        if compact_mode:
            content_section_names = ["tone"]
        else:
            content_section_names = CONTENT_CONTEXT_MAP.get(content_type_key, DEFAULT_CONTEXT_SEQUENCE)
        sections: list[dict[str, Any]] = []

        for section_name in content_section_names:
            if section_name == "tone":
                text = self.builder.get_tone_context(bundle)
                sections.append(self._build_section("tone", text, "brand_config/tone.md"))
            elif section_name == "audience":
                text = self.builder.get_audience_context(bundle, request.audience)
                sections.append(self._build_section("audience", text, "brand_config/audience.md"))
            elif section_name == "positioning":
                text = self.builder.get_positioning_context(bundle)
                sections.append(self._build_section("positioning", text, "brand_config/positioning.md"))
            elif section_name == "content_rules":
                text = self.builder.get_content_rules_context(bundle)
                sections.append(self._build_section("content_rules", text, "brand_config/content_rules.md"))
            elif section_name == "buyer_psychology":
                text = self.builder.get_buyer_psychology_context(bundle)
                sections.append(self._build_section("buyer_psychology", text, "brand_story/buyer_psychology.md"))
            elif section_name == "market":
                text = self.builder.get_market_context(bundle)
                sections.append(self._build_section("market", text, "market/*"))
            elif section_name == "neighborhood":
                location = self._resolve_location(request.location)
                text = self.builder.get_neighborhood_context(bundle, location) if location else ""
                sections.append(self._build_section("neighborhood", text, f"neighborhoods/{location or 'unknown'}"))
            elif section_name == "platform_rules":
                text = self.builder.get_platform_context(bundle, request.platform)
                sections.append(self._build_section("platform_rules", text, "content_examples/platform_rules.md"))
            elif section_name == "visual":
                text = self.builder.get_visual_identity_context(bundle)
                sections.append(self._build_section("visual", text, "brand_config/visual_identity.md"))
            elif section_name == "examples":
                text = self.builder.get_examples_context(bundle)
                sections.append(self._build_section("examples", text, "content_examples/*"))

        if request.extra_context and not compact_mode:
            sections.append(self._build_section("extra_context", self._stringify_extra_context(request.extra_context), "input/extra_context"))

        if not compact_mode:
            sections.append(self._build_section("role_strategy", self._render_role_strategy(role), f"role/{role.name}"))
            sections.append(self._build_section("prompt_version", self._render_prompt_version(version), f"version/{version.version}"))

        return sections

    def _apply_token_budget(self, sections: list[dict[str, Any]], token_budget: int | None) -> list[dict[str, Any]]:
        """Order and trim sections by priority and budget."""

        ordered = sorted(sections, key=lambda item: (SECTION_PRIORITY.get(item["name"], 99), -item["chars"]))
        if token_budget is None:
            return ordered

        running_total = 0
        selected: list[dict[str, Any]] = []
        for section in ordered:
            next_total = running_total + section["chars"]
            if selected and next_total > token_budget:
                continue
            selected.append(section)
            running_total = next_total
        return selected

    def _build_section(self, name: str, text: str, source: str) -> dict[str, Any]:
        """Build a normalized section payload."""

        cleaned = text.strip()
        return {
            "name": name,
            "text": cleaned,
            "source": source,
            "chars": len(cleaned),
        }

    def _cap_sections_to_chars(self, sections: list[dict[str, Any]], max_chars: int) -> list[dict[str, Any]]:
        """Trim a section list to a hard character limit."""

        if max_chars <= 0:
            return []

        remaining = max_chars
        capped: list[dict[str, Any]] = []
        for section in sections:
            if remaining <= 0:
                break
            text = str(section.get("text", "")).strip()
            if not text:
                continue
            if len(text) > remaining:
                text = text[:remaining].rstrip()
            if not text:
                continue
            capped_section = self._build_section(str(section.get("name", "")), text, str(section.get("source", "")))
            capped.append(capped_section)
            remaining -= capped_section["chars"]
        return capped

    def _resolve_location(self, location: str | None) -> str:
        """Normalize a location key for neighborhood lookups."""

        if not location:
            return ""
        return normalize_key(location)

    def _stringify_extra_context(self, extra_context: dict[str, Any]) -> str:
        """Convert extra context into a readable block."""

        lines = []
        for key, value in extra_context.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)

    def _render_role_strategy(self, role: PromptRole) -> str:
        """Render the selected role strategy as prompt-ready text."""

        lines = [
            f"Role: {role.name}",
            f"Tone: {role.tone}",
            f"Vocabulary: {', '.join(role.vocabulary)}" if role.vocabulary else "Vocabulary: none",
            f"Storytelling: {role.storytelling}",
            f"Structure: {role.structure}",
            f"CTA behavior: {role.cta_behavior}",
        ]
        if role.guidance:
            lines.append("Guidance:")
            lines.extend(f"- {item}" for item in role.guidance)
        if role.avoid:
            lines.append("Avoid:")
            lines.extend(f"- {item}" for item in role.avoid)
        return "\n".join(lines)

    def _render_prompt_version(self, version: PromptVersion) -> str:
        """Render the prompt version metadata as prompt-ready text."""

        return (
            f"Version: {version.version}\n"
            f"Content type: {version.content_type}\n"
            f"Platform: {version.platform}\n"
            f"Notes: {version.notes}"
        )
