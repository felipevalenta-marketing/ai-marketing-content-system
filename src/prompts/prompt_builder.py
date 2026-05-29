"""Dynamic prompt orchestration for the AI Marketing Content System."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json

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
        if not bundle.brand_config and not bundle.knowledge_base:
            validation_errors.append(f"Brand context could not be loaded for '{request.brand}'.")
            return self._empty_payload(input_data, validation_errors, brand=request.brand, content_type=request.content_type).to_dict()

        injected = self.injector.inject(bundle, request, token_budget=token_budget)
        if not injected.context_used:
            validation_errors.append("Empty context injection: no markdown context was selected.")

        role = get_role(request.role, request.content_type)
        version = resolve_prompt_version(request.content_type, request.platform)
        contract = get_output_contract(request.content_type)
        template = get_template(request.content_type)
        prompt_mode = self._prompt_mode(request.content_type)
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
        template = get_template(request.content_type)
        return template.render_system(
            **self._build_template_variables(request, injected, role, version, contract, prompt_mode)
        )

    def build_user_prompt(self, request: PromptRequest, injected: InjectedContext) -> str:
        """Build only the user prompt for advanced orchestration."""

        role = get_role(request.role, request.content_type)
        version = resolve_prompt_version(request.content_type, request.platform)
        contract = get_output_contract(request.content_type)
        prompt_mode = self._prompt_mode(request.content_type)
        template = get_template(request.content_type)
        return template.render_user(
            **self._build_template_variables(request, injected, role, version, contract, prompt_mode)
        )

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
                audience=audience,
                location=self._optional_str(input_data.get("location")),
                property_type=self._optional_str(input_data.get("property_type")),
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
        return {
            "brand": request.brand,
            "platform": request.platform,
            "content_type": request.content_type,
            "objective": request.objective,
            "chain_step": request.chain_step or "single_pass",
            "audience_segment": request.audience or "general",
            "location": request.location or "unspecified",
            "property_type": request.property_type or "unspecified",
            "keyword_theme": request.keyword_theme or request.location or request.objective,
            "prompt_version": request.prompt_version or version.version,
            "prompt_mode": prompt_mode,
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
        }

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

    def _prompt_mode(self, content_type: str) -> str:
        """Resolve the prompt mode for a content type."""

        return PROMPT_MODE_MAP.get(content_type, "campaign")

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
