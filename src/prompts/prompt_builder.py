"""Dynamic prompt orchestration for the AI Marketing Content System."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import re

from src.core.knowledge_loader import KnowledgeLoader, load_brand_knowledge
from src.prompts.context_injector import ContextInjector, InjectedContext, PromptRequest
from src.prompts.platform_rules import get_platform_rule, list_supported_platforms
from src.prompts.prompt_contracts import OutputContract, build_output_instructions, get_output_contract
from src.prompts.prompt_governance import build_prompt_governance
from src.prompts.prompt_roles import PromptRole, get_role
from src.prompts.prompt_templates import PromptTemplate, get_template, list_supported_content_types
from src.prompts.prompt_versions import PromptVersion, resolve_prompt_version
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context


PROMPT_MODE_MAP = {
    "instagram_post": "social",
    "instagram_reel": "social",
    "facebook_post": "social",
    "linkedin_post": "social",
    "property_description": "listing",
    "neighborhood_story": "seo",
    "relocation_content": "seo",
    "email_marketing": "campaign",
    "seo_page": "seo",
    "image_prompt": "image",
    "video_prompt": "video",
    "video_script": "video_script",
    "ad_copy": "social",
    "campaign_pack": "campaign",
}

COMPACT_PROMPT_CONTENT_TYPES = {
    "linkedin_post",
    "facebook_post",
    "ad_copy",
    "property_description",
    "image_prompt",
    "video_script",
    "instagram_reel",
}
COMPACT_CONTEXT_CHAR_LIMIT = 1500
COMPACT_PROMPT_CHAR_LIMIT = 8000


DEFAULT_CHAIN_STEPS = {
    "social": ["hook_generation", "caption_generation", "cta_generation", "hashtag_generation"],
    "listing": ["headline_generation", "description_generation", "cta_generation"],
    "seo": ["outline_generation", "section_generation", "cta_generation"],
    "image": ["visual_direction", "composition", "lighting", "camera_style"],
    "video": ["scene_description", "camera_motion", "mood", "voiceover_direction"],
    "video_script": ["hook_generation", "script_generation", "voiceover_direction", "cta_generation", "storyboard_generation"],
    "campaign": ["campaign_angle", "hook_generation", "caption_generation", "cta_generation"],
}


@dataclass(frozen=True)
class PromptOrchestrationMetadata:
    """Observability metadata for prompt assembly."""

    prompt_type: str
    prompt_mode: str
    prompt_version: str
    role_strategy: str
    role_tone: str
    chain_step: str | None
    context_sources_used: list[str]
    injected_categories: list[str]
    estimated_prompt_size: int
    active_platform_rules: list[str]
    template_family: str
    output_contract_name: str
    provider_agnostic: bool = True
    context_preview: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize orchestration metadata."""

        return {
            "prompt_type": self.prompt_type,
            "prompt_mode": self.prompt_mode,
            "prompt_version": self.prompt_version,
            "role_strategy": self.role_strategy,
            "role_tone": self.role_tone,
            "chain_step": self.chain_step,
            "context_sources_used": self.context_sources_used,
            "injected_categories": self.injected_categories,
            "estimated_prompt_size": self.estimated_prompt_size,
            "active_platform_rules": self.active_platform_rules,
            "template_family": self.template_family,
            "output_contract_name": self.output_contract_name,
            "provider_agnostic": self.provider_agnostic,
            "context_preview": self.context_preview,
        }


@dataclass(frozen=True)
class PromptPayload:
    """Structured prompt output returned by the orchestration engine."""

    system_prompt: str
    user_prompt: str
    context_used: list[str]
    platform_rules: list[str]
    content_type: str
    brand: str
    prompt_version: str
    role_strategy: str
    prompt_mode: str
    output_contract: dict[str, Any]
    orchestration_metadata: dict[str, Any]
    prompt_summary: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the prompt payload."""

        payload = {
            "system_prompt": self.system_prompt,
            "user_prompt": self.user_prompt,
            "context_used": self.context_used,
            "platform_rules": self.platform_rules,
            "content_type": self.content_type,
            "brand": self.brand,
            "prompt_version": self.prompt_version,
            "role_strategy": self.role_strategy,
            "prompt_mode": self.prompt_mode,
            "output_contract": self.output_contract,
            "orchestration_metadata": self.orchestration_metadata,
            "metadata": self.orchestration_metadata,
            "prompt_summary": self.prompt_summary,
        }
        if self.errors:
            payload["errors"] = self.errors
        if self.warnings:
            payload["warnings"] = self.warnings
        return payload


class PromptBuilder:
    """Central orchestration engine for AI-ready prompt construction."""

    def __init__(self, brands_root: str | Path | None = None, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.loader = KnowledgeLoader(brands_root=brands_root, logger=self.logger)
        self.injector = ContextInjector(logger=self.logger)

    def build_prompt(self, input_data: dict[str, Any], token_budget: int | None = None) -> dict[str, Any]:
        """Build a prompt payload from structured request input."""

        request, validation_errors = self._build_request(input_data)
        if request is None:
            return self._empty_payload(input_data, validation_errors).to_dict()

        bundle = load_brand_knowledge(request.brand, brands_root=self.loader.brands_root)
        if not bundle.brand_config and not bundle.knowledge_base and any("Brand folder not found" in warning for warning in bundle.warnings):
            validation_errors.append(f"Brand context could not be loaded for '{request.brand}'.")
            return self._empty_payload(input_data, validation_errors, brand=request.brand, content_type=request.content_type).to_dict()

        compact_mode = self._is_compact_content_type(request.content_type)
        injected = self.injector.inject(
            bundle,
            request,
            token_budget=token_budget,
            compact=compact_mode,
        )
        if not injected.context_used:
            validation_errors.append("Empty context injection: no markdown context was selected.")

        role = get_role(request.role, request.content_type)
        version = resolve_prompt_version(request.content_type, request.platform)
        contract = get_output_contract(request.content_type)
        prompt_mode = self._prompt_mode(request.content_type)
        if compact_mode:
            system_prompt, user_prompt = self._build_compact_prompt_strings(request, injected, contract)
            template = self._compact_prompt_template()
        else:
            template = get_template(request.content_type)
            prompt_vars = self._build_template_variables(request, injected, role, version, contract, prompt_mode)
            system_prompt = template.render_system(**prompt_vars)
            user_prompt = template.render_user(**prompt_vars)
        metadata = self._build_orchestration_metadata(
            request=request,
            injected=injected,
            role=role,
            version=version,
            contract=contract,
            prompt_mode=prompt_mode,
            template=template,
        )
        summary = self._build_prompt_summary(request, injected, role, version, contract)
        warnings = list(validation_errors)

        log_context(self.logger, f"Built prompt for {request.brand}/{request.platform}/{request.content_type}")
        return PromptPayload(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            context_used=injected.context_used,
            platform_rules=injected.platform_rules,
            content_type=request.content_type,
            brand=request.brand,
            prompt_version=version.version,
            role_strategy=role.name,
            prompt_mode=prompt_mode,
            output_contract=contract.to_dict(),
            orchestration_metadata=metadata.to_dict(),
            prompt_summary=summary,
            errors=[],
            warnings=warnings if warnings else [],
        ).to_dict()

    def build_prompt_chain(self, input_data: dict[str, Any], steps: list[str] | None = None, token_budget: int | None = None) -> list[dict[str, Any]]:
        """Build a sequence of prompt payloads for chained generation workflows."""

        request, validation_errors = self._build_request(input_data)
        if request is None:
            return [self._empty_payload(input_data, validation_errors).to_dict()]

        chain_steps = steps or self._default_chain_steps(request.content_type)
        chain_payloads: list[dict[str, Any]] = []
        for step in chain_steps:
            step_input = dict(input_data)
            step_input["objective"] = self._objective_for_step(step, request.objective)
            step_input["extra_context"] = self._merge_extra_context(step_input.get("extra_context"), {"chain_step": step})
            step_input["chain_step"] = step
            step_payload = self.build_prompt(step_input, token_budget=token_budget)
            step_payload["chain_step"] = step
            chain_payloads.append(step_payload)
        return chain_payloads

    def build_system_prompt(self, request: PromptRequest, injected: InjectedContext) -> str:
        """Build only the system prompt for advanced orchestration."""

        role = get_role(request.role, request.content_type)
        version = resolve_prompt_version(request.content_type, request.platform)
        contract = get_output_contract(request.content_type)
        prompt_mode = self._prompt_mode(request.content_type)
        if self._is_compact_content_type(request.content_type):
            return self._build_compact_system_prompt(contract)
        template = get_template(request.content_type)
        return template.render_system(**self._build_template_variables(request, injected, role, version, contract, prompt_mode))

    def build_user_prompt(self, request: PromptRequest, injected: InjectedContext) -> str:
        """Build only the user prompt for advanced orchestration."""

        role = get_role(request.role, request.content_type)
        version = resolve_prompt_version(request.content_type, request.platform)
        contract = get_output_contract(request.content_type)
        prompt_mode = self._prompt_mode(request.content_type)
        if self._is_compact_content_type(request.content_type):
            return self._build_compact_user_prompt(request, injected, contract)
        template = get_template(request.content_type)
        return template.render_user(**self._build_template_variables(request, injected, role, version, contract, prompt_mode))

    def describe_prompt_plan(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Return a human-readable orchestration report before generation."""

        request, errors = self._build_request(input_data)
        if request is None:
            return {"errors": errors, "input": input_data}

        role = get_role(request.role, request.content_type)
        version = resolve_prompt_version(request.content_type, request.platform)
        contract = get_output_contract(request.content_type)
        return {
            "brand": request.brand,
            "platform": request.platform,
            "content_type": request.content_type,
            "objective": request.objective,
            "role_strategy": role.to_dict(),
            "prompt_version": version.to_dict(),
            "output_contract": contract.to_dict(),
            "platform_rules": get_platform_rule(request.platform).to_dict(),
            "chain_steps": self._default_chain_steps(request.content_type),
        }

    def _build_request(self, input_data: dict[str, Any]) -> tuple[PromptRequest | None, list[str]]:
        """Validate raw input and convert it into a structured request."""

        errors: list[str] = []
        brand = self._normalize_required_str(input_data.get("brand"), "brand", errors)
        platform = self._normalize_required_str(input_data.get("platform"), "platform", errors)
        content_type = self._normalize_required_str(input_data.get("content_type"), "content_type", errors)
        objective = self._required_str(input_data.get("objective"), "objective", errors)
        audience = self._required_str(input_data.get("audience"), "audience", errors)
        prompt_text = self._normalize_prompt_text(input_data.get("prompt") or input_data.get("extra_notes") or objective)
        extracted = self._extract_prompt_details(
            prompt_text,
            fallback_location=self._optional_str(input_data.get("location")),
            fallback_property_type=self._optional_str(input_data.get("property_type")),
            fallback_audience=audience,
        )

        if brand and brand not in self.loader.detect_brands():
            errors.append(f"Unsupported brand: {brand}")
        if platform and platform not in list_supported_platforms():
            errors.append(f"Unsupported platform: {platform}")
        if content_type and content_type not in list_supported_content_types():
            errors.append(f"Unsupported content_type: {content_type}")
        if input_data.get("extra_context") is not None and not isinstance(input_data.get("extra_context"), dict):
            errors.append("extra_context must be a dictionary when provided")

        if errors:
            return None, errors

        return (
            PromptRequest(
                brand=brand,
                platform=platform,
                content_type=content_type,
                objective=objective,
                prompt=prompt_text,
                audience=extracted["audience"] or audience,
                location=extracted["location"] or self._optional_str(input_data.get("location")),
                property_type=extracted["property_type"] or self._optional_str(input_data.get("property_type")),
                keyword_theme=self._optional_str(input_data.get("keyword_theme")),
                role=self._optional_str(input_data.get("role")),
                prompt_version=self._optional_str(input_data.get("prompt_version")),
                chain_step=self._optional_str(input_data.get("chain_step")),
                extra_context=dict(input_data.get("extra_context", {})) if isinstance(input_data.get("extra_context", {}), dict) else {},
            ),
            errors,
        )

    def _build_template_variables(
        self,
        request: PromptRequest,
        injected: InjectedContext,
        role: PromptRole,
        version: PromptVersion,
        contract: OutputContract,
        prompt_mode: str,
    ) -> dict[str, Any]:
        """Build the variables used by the prompt templates."""

        sections = injected.sections
        prompt_text = self._normalize_prompt_text(
            request.prompt
            or request.extra_context.get("prompt")
            or request.extra_context.get("extra_notes")
            or request.objective
        )
        extracted = self._extract_prompt_details(
            prompt_text,
            fallback_location=request.location,
            fallback_property_type=request.property_type,
            fallback_audience=request.audience,
        )
        return {
            "brand": request.brand,
            "platform": request.platform,
            "content_type": request.content_type,
            "objective": request.objective,
            "prompt": prompt_text,
            "chain_step": request.chain_step or "single_pass",
            "audience_segment": extracted["audience"] or request.audience or "general",
            "location": extracted["location"] or request.location or "unspecified",
            "property_type": extracted["property_type"] or request.property_type or "unspecified",
            "keyword_theme": request.keyword_theme or extracted["location"] or request.objective,
            "extracted_details": self._render_extracted_details(extracted),
            "prompt_version": request.prompt_version or version.version,
            "prompt_mode": prompt_mode,
            "copy_quality_rules": self._render_copy_quality_rules(request, injected, role),
            "hook_guidance": self._render_hook_guidance(request, extracted, injected, role),
            "cta_guidance": self._render_cta_guidance(request, extracted, injected, role),
            "feature_inventory": self._render_feature_inventory(request, extracted, injected),
            "role_strategy": self._render_role_strategy(role),
            "context_injection": self._format_context_injection(sections),
            "context_block": self._format_context_injection(sections),
            "tone": sections.get("tone", ""),
            "positioning": sections.get("positioning", ""),
            "audience": sections.get("audience", ""),
            "buyer_psychology": sections.get("buyer_psychology", ""),
            "market": sections.get("market", ""),
            "neighborhood": sections.get("neighborhood", ""),
            "content_rules": sections.get("content_rules", ""),
            "platform_rules": self._render_platform_rule(get_platform_rule(request.platform), injected.platform_rules, sections.get("platform_rules", "")),
            "visual": sections.get("visual", ""),
            "governance": build_prompt_governance(request.content_type),
            "output_instructions": build_output_instructions(request.content_type),
            "output_formatting": self._render_output_formatting(contract),
            "output_json_keys": self._render_output_json_keys(contract),
            "output_json_example": self._render_output_json_example(contract),
        }

    def _build_compact_prompt_strings(self, request: PromptRequest, injected: InjectedContext, contract: OutputContract) -> tuple[str, str]:
        """Build compact prompts for media generation types."""

        prompt_text = self._normalize_prompt_text(
            request.prompt
            or request.extra_context.get("prompt")
            or request.extra_context.get("extra_notes")
            or request.objective
        )
        extracted = self._extract_prompt_details(
            prompt_text,
            fallback_location=request.location,
            fallback_property_type=request.property_type,
            fallback_audience=request.audience,
        )
        context_block = self._build_compact_context_block(injected, max_chars=COMPACT_CONTEXT_CHAR_LIMIT)
        system_prompt = self._build_compact_system_prompt(contract)
        user_prompt = self._build_compact_user_prompt_from_parts(
            brand=request.brand,
            content_type=request.content_type,
            platform=request.platform,
            prompt_text=prompt_text,
            location=extracted["location"] or request.location or "unspecified",
            property_type=extracted["property_type"] or request.property_type or "unspecified",
            audience=extracted["audience"] or request.audience or "general",
            context_block=context_block,
        )
        system_prompt, user_prompt = self._enforce_compact_prompt_limit(system_prompt, user_prompt, prompt_text)
        return system_prompt, user_prompt

    def _build_compact_system_prompt(self, contract: OutputContract) -> str:
        """Render the minimal system prompt for compact media generation."""

        return (
            "You are a compact real-estate content generator.\n"
            "Use only the user prompt, brand name, platform, extracted location, property type, audience, and the brief brand tone bullets.\n"
            "Do not inject knowledge base, examples, market reports, neighborhood reports, governance, or long brand context.\n"
            "Avoid generic phrases such as dream home, epitome of luxury, unparalleled luxury, and elevate your lifestyle.\n"
            "Prefer specific property features and audience fit over broad luxury language.\n"
            "Return only valid JSON with exactly these keys:\n"
            f"{self._render_output_json_keys(contract)}\n"
            "Do not add markdown, commentary, or extra keys."
        ).strip()

    def _build_compact_user_prompt(
        self,
        request: PromptRequest,
        injected: InjectedContext,
        contract: OutputContract,
    ) -> str:
        """Render the compact user prompt for media generation."""

        prompt_text = self._normalize_prompt_text(
            request.prompt
            or request.extra_context.get("prompt")
            or request.extra_context.get("extra_notes")
            or request.objective
        )
        extracted = self._extract_prompt_details(
            prompt_text,
            fallback_location=request.location,
            fallback_property_type=request.property_type,
            fallback_audience=request.audience,
        )
        context_block = self._build_compact_context_block(injected, max_chars=COMPACT_CONTEXT_CHAR_LIMIT)
        return self._build_compact_user_prompt_from_parts(
            brand=request.brand,
            content_type=request.content_type,
            platform=request.platform,
            prompt_text=prompt_text,
            location=extracted["location"] or request.location or "unspecified",
            property_type=extracted["property_type"] or request.property_type or "unspecified",
            audience=extracted["audience"] or request.audience or "general",
            context_block=context_block,
        )

    def _build_compact_user_prompt_from_parts(
        self,
        *,
        brand: str,
        content_type: str,
        platform: str,
        prompt_text: str,
        location: str,
        property_type: str,
        audience: str,
        context_block: str,
    ) -> str:
        """Render the compact user prompt from sanitized pieces."""

        return (
            "User prompt:\n"
            f"{prompt_text}\n"
            f"Brand: {brand}\n"
            f"Content type: {content_type}\n"
            f"Platform: {platform}\n"
            f"Location: {location}\n"
            f"Property type: {property_type}\n"
            f"Audience: {audience}\n"
            f"Context block:\n{context_block}"
        ).strip()

    def _build_compact_context_block(self, injected: InjectedContext, max_chars: int = COMPACT_CONTEXT_CHAR_LIMIT) -> str:
        """Turn the brand tone into a small bullet list for compact prompts."""

        tone_text = str(injected.sections.get("tone", "") or "").strip()
        bullets = self._extract_compact_bullets(tone_text, max_items=5)
        if not bullets:
            fallback = tone_text or "Use a calm, premium, grounded real-estate tone."
            bullets = [fallback]
        context_block = "\n".join(f"- {bullet}" for bullet in bullets)
        return self._trim_text(context_block, max_chars)

    def _extract_compact_bullets(self, text: str, max_items: int = 5) -> list[str]:
        """Extract short tone bullets from a longer brand tone block."""

        if not text.strip():
            return []

        candidates: list[str] = []
        for line in text.splitlines():
            candidate = line.strip().lstrip("-•*").strip()
            if candidate:
                candidates.append(candidate)

        if not candidates:
            sentences = [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]
            candidates = sentences

        bullets: list[str] = []
        for candidate in candidates:
            normalized = " ".join(candidate.split())
            if not normalized or normalized in bullets:
                continue
            bullets.append(self._trim_text(normalized, 140))
            if len(bullets) >= max_items:
                break
        return bullets

    def _enforce_compact_prompt_limit(self, system_prompt: str, user_prompt: str, prompt_text: str) -> tuple[str, str]:
        """Hard-cap compact prompts to the requested combined length."""

        combined = len(system_prompt) + len(user_prompt)
        if combined <= COMPACT_PROMPT_CHAR_LIMIT:
            return system_prompt, user_prompt

        prompt_budget = max(0, COMPACT_PROMPT_CHAR_LIMIT - (combined - len(prompt_text)))
        trimmed_prompt = self._trim_text(prompt_text, prompt_budget)
        if trimmed_prompt != prompt_text:
            user_prompt = user_prompt.replace(prompt_text, trimmed_prompt, 1)
            combined = len(system_prompt) + len(user_prompt)
        if combined <= COMPACT_PROMPT_CHAR_LIMIT:
            return system_prompt, user_prompt

        overflow = combined - COMPACT_PROMPT_CHAR_LIMIT
        user_prompt = self._trim_text(user_prompt, max(0, len(user_prompt) - overflow))
        return system_prompt, user_prompt

    def _compact_prompt_template(self) -> PromptTemplate:
        """Return a synthetic template used for compact prompt metadata."""

        return PromptTemplate(name="compact", system_template="", user_template="", description="Compact media generation prompt.")

    def _build_orchestration_metadata(
        self,
        request: PromptRequest,
        injected: InjectedContext,
        role: PromptRole,
        version: PromptVersion,
        contract: OutputContract,
        prompt_mode: str,
        template: PromptTemplate,
    ) -> PromptOrchestrationMetadata:
        """Build observability metadata for the prompt assembly."""

        return PromptOrchestrationMetadata(
            prompt_type=request.content_type,
            prompt_mode=prompt_mode,
            prompt_version=version.version,
            role_strategy=role.name,
            role_tone=role.tone,
            chain_step=request.chain_step,
            context_sources_used=injected.context_used,
            injected_categories=injected.injected_categories,
            estimated_prompt_size=injected.token_estimate + len(request.objective) + len(request.brand),
            active_platform_rules=injected.platform_rules,
            template_family=template.name,
            output_contract_name=contract.name,
            context_preview=injected.source_preview,
        )

    def _build_prompt_summary(
        self,
        request: PromptRequest,
        injected: InjectedContext,
        role: PromptRole,
        version: PromptVersion,
        contract: OutputContract,
    ) -> str:
        """Build a concise prompt summary for developer experience."""

        return (
            f"{request.brand}/{request.platform}/{request.content_type} | "
            f"role={role.name} | version={version.version} | "
            f"sections={len(injected.sections)} | contract={contract.name} | "
            f"est_chars={injected.token_estimate}"
        )

    def _format_context_injection(self, sections: dict[str, str]) -> str:
        """Render the selected sections into a compact readable block."""

        lines: list[str] = []
        for key, value in sections.items():
            if not value.strip():
                continue
            lines.append(f"## {key.replace('_', ' ').title()}\n{value}")
        return "\n\n".join(lines)

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

    def _render_copy_quality_rules(self, request: PromptRequest, injected: InjectedContext, role: PromptRole) -> str:
        """Render copy quality rules that keep the output specific and feature-led."""

        lines = [
            "Lead with concrete property facts before any emotional framing.",
            "Use location, audience and property attributes when they are available.",
            "Translate each hook into a visible feature, benefit or buyer fit.",
            "Avoid vague luxury superlatives unless the prompt explicitly supports them.",
        ]
        if request.location:
            lines.append(f"- Location signal: {request.location}")
        if request.property_type:
            lines.append(f"- Property type signal: {request.property_type}")
        if request.audience:
            lines.append(f"- Audience signal: {request.audience}")
        if injected.context_used:
            lines.append(f"- Context sources available: {len(injected.context_used)}")
        if role.guidance:
            lines.extend(f"- Role guidance: {item}" for item in role.guidance[:3])
        return "\n".join(lines)

    def _render_hook_guidance(self, request: PromptRequest, extracted: dict[str, str], injected: InjectedContext, role: PromptRole) -> str:
        """Render hook guidance that favors specific details over generic luxury copy."""

        signals = [item for item in [extracted.get("location"), extracted.get("property_type"), extracted.get("audience"), request.keyword_theme] if item]
        lines = [
            "Start with the most distinctive fact in the prompt.",
            "Prefer a concrete feature, neighborhood cue, or buyer fit over abstract luxury language.",
            "Keep the first sentence short, vivid and specific.",
        ]
        if signals:
            lines.append(f"Feature signals: {', '.join(signals)}")
        if injected.source_preview:
            preview_bits = [value for value in injected.source_preview.values() if value]
            if preview_bits:
                lines.append(f"Source cues: {preview_bits[0][:160]}")
        if role.avoid:
            lines.append(f"Avoid language such as: {', '.join(role.avoid[:3])}")
        return "\n".join(lines)

    def _render_cta_guidance(self, request: PromptRequest, extracted: dict[str, str], injected: InjectedContext, role: PromptRole) -> str:
        """Render CTA guidance that stays practical and audience-aware."""

        audience = extracted.get("audience") or request.audience or "the audience"
        location = extracted.get("location") or request.location
        property_type = extracted.get("property_type") or request.property_type
        lines = [
            "Keep the CTA direct, active and easy to act on.",
            f"Address {audience} with the next obvious step.",
        ]
        if location or property_type:
            lines.append(f"Reference {location or 'the location'} and {property_type or 'the property'} when it improves clarity.")
        if injected.context_used:
            lines.append("Tie the CTA to the strongest real detail from the prompt, not a generic luxury promise.")
        if role.cta_behavior:
            lines.append(f"Role CTA behavior: {role.cta_behavior}")
        return "\n".join(lines)

    def _render_feature_inventory(self, request: PromptRequest, extracted: dict[str, str], injected: InjectedContext) -> str:
        """Render a concise feature inventory derived from the user prompt and injected context."""

        inventory: list[str] = []
        for value in [request.location, request.property_type, request.audience, request.keyword_theme, extracted.get("location"), extracted.get("property_type"), extracted.get("audience")]:
            if value and value not in inventory:
                inventory.append(value)
        feature_sources = request.extra_context.get("features") or request.extra_context.get("highlights") or request.extra_context.get("amenities")
        if isinstance(feature_sources, (list, tuple, set)):
            for item in feature_sources:
                text = self._optional_str(item)
                if text and text not in inventory:
                    inventory.append(text)
        elif isinstance(feature_sources, str):
            for part in re.split(r"[,;•\n]", feature_sources):
                text = self._optional_str(part)
                if text and text not in inventory:
                    inventory.append(text)
        if injected.source_preview.get("visual"):
            visual_preview = injected.source_preview["visual"].strip()
            if visual_preview and visual_preview not in inventory:
                inventory.append(visual_preview)
        if not inventory:
            inventory.append("No explicit feature inventory provided; rely only on the prompt details and injected context.")
        return "\n".join(f"- {item}" for item in inventory[:8])

    def _render_platform_rule(self, platform_rule: Any, platform_rules: list[str], platform_section: str) -> str:
        """Combine platform guidance into a prompt-ready block."""

        lines = [
            f"Platform behavior: {platform_rule.tone}",
            f"Structure: {platform_rule.structure}",
            f"CTA style: {platform_rule.cta_style}",
            f"Length: {platform_rule.length}",
            f"Storytelling depth: {platform_rule.storytelling_depth}",
        ]
        if platform_rules:
            lines.append("Guidance:")
            lines.extend(f"- {item}" for item in platform_rules[1:] if item)
        if platform_section.strip():
            lines.append("")
            lines.append(platform_section.strip())
        return "\n".join(lines).strip()

    def _render_output_formatting(self, contract: OutputContract) -> str:
        """Render output formatting instructions for the system prompt."""

        return contract.to_instruction_block()

    def _render_output_json_keys(self, contract: OutputContract) -> str:
        """Render the exact JSON keys expected from the model."""

        lines = ["{"]
        for index, field_name in enumerate(contract.fields):
            suffix = "," if index < len(contract.fields) - 1 else ""
            lines.append(f'  "{field_name}": "..."{suffix}')
        lines.append("}")
        return "\n".join(lines)

    def _render_output_json_example(self, contract: OutputContract) -> str:
        """Render a compact example payload for the expected JSON output."""

        example_map = {
            "image_prompt": {
                "image_prompt": "Premium Mallorca exterior with realistic architectural detail.",
                "style": "Mediterranean lifestyle",
                "camera": "Wide-angle exterior photography",
                "lighting": "Natural daylight",
                "negative_prompt": "blurry, low quality, CGI, text overlays",
            },
            "video_script": {
                "hook": "A calm look at a Mallorca home that feels made for real life.",
                "scene_1": "Exterior reveal with clean architectural framing.",
                "scene_2": "Interior sweep showing light, space, and lifestyle fit.",
                "scene_3": "Final closing shot with location context and brand reassurance.",
                "voiceover": "A calm, premium property story with a clear buyer benefit.",
                "cta": "Send us a message to learn more.",
            },
            "instagram_post": {
                "hook": "Discover Mallorca living",
                "caption": "A calm, practical home with real lifestyle appeal.",
                "cta": "Request a viewing",
                "hashtags": ["#Mallorca", "#RealEstate", "#Lifestyle"],
            },
        }
        example = example_map.get(contract.content_type)
        if example is None:
            example = {field: "..." for field in contract.fields}
        return json.dumps(example, indent=2, ensure_ascii=False)

    def _trim_text(self, text: str, max_chars: int) -> str:
        """Trim text to a maximum number of characters while keeping it readable."""

        if max_chars <= 0:
            return ""
        cleaned = str(text or "")
        if len(cleaned) <= max_chars:
            return cleaned
        trimmed = cleaned[:max_chars].rstrip()
        return trimmed[:-3].rstrip() + "..." if len(trimmed) > 3 else trimmed

    def _normalize_prompt_text(self, prompt_text: str) -> str:
        """Normalize raw prompt text before injection."""

        return " ".join(str(prompt_text or "").split()).strip()

    def _extract_prompt_details(
        self,
        prompt_text: str,
        *,
        fallback_location: str | None = None,
        fallback_property_type: str | None = None,
        fallback_audience: str | None = None,
    ) -> dict[str, str]:
        """Extract high-priority prompt details from the user prompt."""

        normalized = prompt_text.strip()
        if not normalized:
            return {
                "location": self._optional_str(fallback_location) or "",
                "property_type": self._optional_str(fallback_property_type) or "",
                "audience": self._optional_str(fallback_audience) or "",
                "signals": "",
            }

        location = self._extract_location(normalized) or self._optional_str(fallback_location) or ""
        property_type = self._extract_property_type(normalized) or self._optional_str(fallback_property_type) or ""
        audience = self._extract_audience(normalized) or self._optional_str(fallback_audience) or ""
        signals = ", ".join(part for part in [location, property_type, audience] if part)
        return {
            "location": location,
            "property_type": property_type,
            "audience": audience,
            "signals": signals,
        }

    def _render_extracted_details(self, details: dict[str, str]) -> str:
        """Render extracted prompt details into a readable block."""

        lines = [
            f"- Location: {details.get('location') or 'unspecified'}",
            f"- Property type: {details.get('property_type') or 'unspecified'}",
            f"- Audience: {details.get('audience') or 'general'}",
        ]
        if details.get("signals"):
            lines.append(f"- Key signals: {details['signals']}")
        lines.append("- Preserve these details exactly; do not replace them with brand examples or knowledge-base locations.")
        return "\n".join(lines)

    def _extract_location(self, text: str) -> str:
        """Extract likely location phrases from a user prompt."""

        patterns = [
            r"(?:\bin\b|\boverlooking\b|\bnear\b|\baround\b|\bat\b)\s+([A-Z][A-Za-z0-9'’&.-]+(?:\s+[A-Z][A-Za-z0-9'’&.-]+){0,4})",
            r"([A-Z][A-Za-z0-9'’&.-]+(?:\s+[A-Z][A-Za-z0-9'’&.-]+){0,4})\s+(?:overlooking|with|for)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                candidate = match.group(1).strip(" ,.;:-")
                if candidate:
                    return candidate
        return ""

    def _extract_property_type(self, text: str) -> str:
        """Extract likely property type keywords from a user prompt."""

        property_types = [
            "penthouse",
            "villa",
            "apartment",
            "home",
            "house",
            "loft",
            "townhouse",
            "condo",
            "studio",
            "duplex",
            "chalet",
            "estate",
            "mansion",
            "finca",
        ]
        lowered = text.lower()
        for property_type in property_types:
            if property_type in lowered:
                return property_type
        return ""

    def _extract_audience(self, text: str) -> str:
        """Extract likely audience phrases from a user prompt."""

        audience_keywords = ("buyers", "clients", "investors", "families", "developers", "renters", "tenants", "owners", "relocators")
        patterns = [
            r"\b(?:target|for|to)\s+(.+?)(?:[.;]|$)",
            r"\b(?:targeting|aimed at)\s+(.+?)(?:[.;]|$)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                candidate = match.group(1).strip(" ,.;:-")
                if any(keyword in candidate.lower() for keyword in audience_keywords):
                    return candidate
        return ""

    def _prompt_mode(self, content_type: str) -> str:
        """Resolve the prompt mode for a content type."""

        return PROMPT_MODE_MAP.get(content_type, "campaign")

    def _is_compact_content_type(self, content_type: str) -> bool:
        """Return whether the content type should use compact prompt assembly."""

        return normalize_key(content_type) in COMPACT_PROMPT_CONTENT_TYPES

    def _default_chain_steps(self, content_type: str) -> list[str]:
        """Return the default chain steps for a content type."""

        mode = self._prompt_mode(content_type)
        return DEFAULT_CHAIN_STEPS.get(mode, DEFAULT_CHAIN_STEPS["campaign"])

    def _objective_for_step(self, step: str, objective: str) -> str:
        """Translate a chain step into a step-specific objective."""

        step_map = {
            "hook_generation": "Generate a strong hook",
            "caption_generation": "Write the caption",
            "cta_generation": "Create the CTA",
            "hashtag_generation": "Generate supporting hashtags",
            "image_prompt_generation": "Generate the image prompt",
            "visual_direction": "Define the visual direction",
            "composition": "Refine the composition",
            "lighting": "Specify lighting and mood",
            "camera_style": "Specify camera style",
            "scene_description": "Write the scene description",
            "camera_motion": "Describe camera motion",
            "mood": "Define the mood",
            "voiceover_direction": "Guide the voiceover",
            "script_generation": "Write the script",
            "storyboard_generation": "Plan the storyboard",
            "headline_generation": "Generate the headline",
            "description_generation": "Write the description",
            "outline_generation": "Create the outline",
            "section_generation": "Write the section content",
            "campaign_angle": "Define the campaign angle",
        }
        prefix = step_map.get(step, step.replace("_", " ").title())
        return f"{prefix} for: {objective}"

    def _merge_extra_context(self, extra_context: Any, additions: dict[str, Any]) -> dict[str, Any]:
        """Merge optional extra context with chain step metadata."""

        merged: dict[str, Any] = {}
        if isinstance(extra_context, dict):
            merged.update(extra_context)
        merged.update(additions)
        return merged

    def _required_str(self, value: Any, field_name: str, errors: list[str]) -> str:
        """Validate a required string field."""

        text = self._optional_str(value)
        if not text:
            errors.append(f"Missing required field: {field_name}")
            return ""
        return text

    def _normalize_required_str(self, value: Any, field_name: str, errors: list[str]) -> str:
        """Validate and normalize a required key-like string field."""

        text = self._required_str(value, field_name, errors)
        return normalize_key(text) if text else ""

    def _optional_str(self, value: Any) -> str | None:
        """Convert an optional field to a stripped string."""

        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _empty_payload(self, input_data: dict[str, Any], errors: list[str], brand: str = "", content_type: str = "") -> PromptPayload:
        """Create an empty payload when validation fails."""

        content_type_value = content_type or self._optional_str(input_data.get("content_type")) or ""
        return PromptPayload(
            system_prompt="",
            user_prompt="",
            context_used=[],
            platform_rules=[],
            content_type=content_type_value,
            brand=brand or self._optional_str(input_data.get("brand")) or "",
            prompt_version="",
            role_strategy="",
            prompt_mode="",
            output_contract=get_output_contract(content_type_value).to_dict() if content_type_value else {},
            orchestration_metadata={},
            prompt_summary="",
            errors=errors,
            warnings=[],
        )


if __name__ == "__main__":
    logger = get_logger("prompt_builder_demo")
    builder = PromptBuilder(logger=logger)
    brands = builder.loader.detect_brands()
    brand_name = "wenzel_partner" if "wenzel_partner" in brands else (brands[0] if brands else "")

    if not brand_name:
        print("No brands available for prompt demo.")
    else:
        print("Demo brand:", brand_name)
        print("Prompt plan preview:")
        print(json.dumps(builder.describe_prompt_plan(
            {
                "brand": brand_name,
                "platform": "instagram",
                "content_type": "instagram_reel",
                "objective": "generate_leads",
                "audience": "relocation_clients",
                "location": "santa_catalina",
                "property_type": "apartment",
            }
        ), indent=2, ensure_ascii=False)[:3000])
        instagram_payload = builder.build_prompt(
            {
                "brand": brand_name,
                "platform": "instagram",
                "content_type": "instagram_reel",
                "objective": "generate_leads",
                "audience": "relocation_clients",
                "location": "santa_catalina",
                "property_type": "apartment",
            }
        )
        image_payload = builder.build_prompt(
            {
                "brand": brand_name,
                "platform": "image",
                "content_type": "image_prompt",
                "objective": "create_visual_direction",
                "audience": "second_home_buyers",
                "location": "portixol",
                "property_type": "sea_view_apartment",
            }
        )
        print("Instagram prompt payload:")
        print(json.dumps(instagram_payload, indent=2, ensure_ascii=False)[:4000])
        print("Image prompt payload:")
        print(json.dumps(image_payload, indent=2, ensure_ascii=False)[:4000])
