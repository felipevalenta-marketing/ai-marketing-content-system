"""High-level orchestration for deterministic image prompt generation."""

from __future__ import annotations

from typing import Any

from src.media.cinematic_rules import resolve_cinematic_rules
from src.media.image_prompt_contracts import (
    build_image_prompt_request_contract,
    build_image_prompt_response_contract,
    get_supported_aspect_ratios,
    get_supported_image_prompt_types,
    get_supported_platforms,
    normalize_aspect_ratio,
    normalize_image_type,
)
from src.media.image_prompt_validator import ImagePromptValidator
from src.media.negative_prompts import build_negative_prompt
from src.media.prompt_enhancer import PromptEnhancer
from src.media.visual_styles import DEFAULT_VISUAL_STYLE, get_visual_style
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context, log_warning


DEFAULT_CAMERA_DIRECTION = "Natural architectural photography with a realistic camera angle."


class ImagePromptEngine:
    """Create premium, realistic, platform-aware image prompt instructions."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.enhancer = PromptEnhancer()
        self.validator = ImagePromptValidator()

    def generate_image_prompt(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate a structured image prompt from a request or existing asset data."""

        valid, reason = self.validate_request(request)
        normalized = self._normalize_request(request)
        log_context(self.logger, f"Generating image prompt for {normalized['platform']}/{normalized['image_type']}")
        warnings: list[str] = []
        errors: list[str] = []

        style = self.select_visual_style(normalized)
        rules = self.apply_cinematic_rules(normalized, style)
        base_prompt = self.build_prompt(normalized, style, rules)
        if normalized.get("enable_cinematic_enhancement", True):
            prompt = self.enhancer.enhance(base_prompt, style, rules.get("rules", []), normalized)
        else:
            prompt = self.enhancer.clean_prompt(base_prompt)
        negative_prompt = self.build_negative_prompt(normalized)
        requested_style = normalize_key(str(request.get("visual_style") or request.get("style") or DEFAULT_VISUAL_STYLE))
        if requested_style and requested_style != style.get("name", DEFAULT_VISUAL_STYLE):
            warnings.append(f"Unsupported visual style '{requested_style}' replaced with '{style.get('name', DEFAULT_VISUAL_STYLE)}'.")
        validation_payload = {
            "brand": normalized["brand"],
            "platform": normalized["platform"],
            "content_type": "image_prompt",
            "image_type": normalized["image_type"],
            "prompt": prompt,
            "negative_prompt": negative_prompt if normalized.get("enable_negative_prompts", True) else "",
            "visual_style": style.get("name", ""),
            "lighting_style": style.get("lighting", ""),
            "composition_style": style.get("composition", ""),
            "camera_direction": normalized["camera_direction"],
            "aspect_ratio": normalized["aspect_ratio"],
            "enable_negative_prompts": normalized.get("enable_negative_prompts", True),
            "metadata": {
                "objective": normalized.get("objective", ""),
                "audience": normalized.get("audience", ""),
                "location": normalized.get("location", ""),
                "property_type": normalized.get("property_type", ""),
            },
        }
        validation_result = self.validator.validate(validation_payload)
        warnings.extend(validation_result.get("warnings", []))
        errors.extend(validation_result.get("errors", []))
        if not valid and reason:
            errors.append(reason)
        elif reason:
            warnings.append(reason)
        if not prompt:
            errors.append("Image prompt generation produced an empty prompt.")

        result = self.build_result(
            success=not errors and validation_result.get("valid", False),
            prompt=prompt,
            negative_prompt=negative_prompt if normalized.get("enable_negative_prompts", True) else "",
            visual_style=style.get("name", ""),
            lighting_style=style.get("lighting", ""),
            composition_style=style.get("composition", ""),
            camera_direction=normalized["camera_direction"],
            aspect_ratio=normalized["aspect_ratio"],
            platform=normalized["platform"],
            image_type=normalized["image_type"],
            metadata=self._build_metadata(normalized, style, rules),
            warnings=warnings,
            errors=errors,
            cinematic_rules_applied=[rule.get("name", "") for rule in rules.get("rules", [])],
            validation_result=validation_result,
        )
        log_context(self.logger, f"Image prompt ready for {normalized['brand']}/{normalized['image_type']}")
        return result

    def validate_request(self, request: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate the incoming request before prompt generation."""

        if not isinstance(request, dict):
            return False, "Image prompt request must be a dictionary."
        brand = normalize_key(str(request.get("brand", "")))
        platform = normalize_key(str(request.get("platform", "")))
        image_type = normalize_image_type(str(request.get("image_type") or request.get("content_type") or ""))
        aspect_ratio = normalize_aspect_ratio(str(request.get("aspect_ratio") or ""))
        creative_direction = str(request.get("creative_direction", "")).strip()
        visual_style = str(request.get("visual_style", "")).strip()

        if not brand:
            return False, "Missing brand."
        if not platform:
            return False, "Missing platform."
        if platform not in get_supported_platforms():
            return False, f"Unsupported platform: {platform}"
        warnings: list[str] = []
        if not image_type:
            warnings.append("Missing image_type; using a generic visual concept.")
        elif image_type not in get_supported_image_prompt_types():
            warnings.append(f"Unsupported image_type: {image_type}; using a generic visual concept.")
        if not aspect_ratio:
            warnings.append("Missing aspect_ratio; using the default ratio.")
        elif aspect_ratio not in get_supported_aspect_ratios():
            warnings.append(f"Unsupported aspect ratio: {aspect_ratio}; using the default ratio.")
        if not creative_direction:
            warnings.append("Missing creative_direction; using contextual fallback guidance.")
        if not visual_style:
            warnings.append("Missing visual_style; using the default style.")
        return True, "; ".join(warnings) if warnings else None

    def select_visual_style(self, request: dict[str, Any]) -> dict[str, Any]:
        """Select a style preset based on request hints and fallback defaults."""

        requested_style = str(request.get("visual_style") or request.get("style") or DEFAULT_VISUAL_STYLE).strip()
        style = get_visual_style(requested_style)
        if requested_style and style.get("name") != normalize_key(requested_style):
            log_warning(self.logger, f"Unsupported visual style '{requested_style}', using {style.get('name', DEFAULT_VISUAL_STYLE)} instead.")
        return style

    def apply_cinematic_rules(self, request: dict[str, Any], style: dict[str, Any]) -> dict[str, Any]:
        """Resolve cinematic rules compatible with the request."""

        rules = resolve_cinematic_rules(request.get("image_type", ""), request.get("platform", ""), style.get("name", ""))
        return {
            "rules": rules,
            "prompt_fragments": [rule.get("prompt_fragment", "") for rule in rules if rule.get("prompt_fragment")],
        }

    def build_prompt(self, request: dict[str, Any], style: dict[str, Any], rules: dict[str, Any]) -> str:
        """Build the base prompt before enhancement."""

        image_type = str(request.get("image_type", "")).strip()
        platform = str(request.get("platform", "")).strip()
        location = str(request.get("location", "")).strip()
        property_type = str(request.get("property_type", "")).strip()
        creative_direction = str(request.get("creative_direction", "")).strip()
        objective = str(request.get("objective", "")).strip()
        audience = str(request.get("audience", "")).strip()
        aspect_ratio = str(request.get("aspect_ratio", "")).strip()

        components = [
            f"Create a premium, realistic, English-first image prompt for {platform} in the {image_type} category.",
            f"Use the visual style '{style.get('name', DEFAULT_VISUAL_STYLE)}' with {style.get('mood', '')}.",
            f"Lighting: {style.get('lighting', '')}. Composition: {style.get('composition', '')}.",
            f"Camera direction: {DEFAULT_CAMERA_DIRECTION}",
            f"Aspect ratio: {aspect_ratio}.",
        ]
        image_type_specific = {
            "property_exterior": "Focus on grounded architectural realism, clean facade lines, and believable surrounding context.",
            "property_interior": "Show layered interior depth, natural light, and believable material finishes.",
            "lifestyle_scene": "Include authentic human-scale lifestyle cues without staged exaggeration.",
            "architectural_detail": "Emphasize a close-up of a refined architectural detail with precise material texture.",
            "drone_view": "Use a realistic aerial view that shows the property context and surrounding landscape.",
            "neighborhood_scene": "Show the neighborhood character with calm local detail and realistic scale.",
            "reform_potential": "Highlight renovation potential with honest before-and-after energy and realistic structure.",
            "luxury_listing": "Frame the property like a premium listing portal image, polished but not exaggerated.",
            "social_media_visual": "Keep the image emotionally appealing and optimized for social feed impact.",
            "campaign_hero_image": "Make the image work as a campaign hero visual with clean brand presence and strong composition.",
        }
        if image_type in image_type_specific:
            components.append(image_type_specific[image_type])
        if property_type:
            components.append(f"Reference the property type as {property_type} without inventing features.")
        if location:
            components.append(f"Keep the setting grounded in {location} without adding unverified facts.")
        if audience:
            components.append(f"Audience context: {audience}.")
        if objective:
            components.append(f"Objective context: {objective}.")
        if creative_direction:
            components.append(f"Creative direction: {creative_direction}.")
        if rules.get("prompt_fragments"):
            components.append("Cinematic rules: " + " ".join(rules["prompt_fragments"]))
        components.append("Emphasize realistic architectural photography, believable textures, natural light, and premium but approachable realism.")
        components.append("Avoid CGI look, fantasy interiors, fake luxury, impossible architecture, and unsupported claims.")
        return " ".join(part for part in components if part).strip()

    def build_negative_prompt(self, request: dict[str, Any]) -> str:
        """Build a combined negative prompt."""

        return build_negative_prompt(
            image_type=str(request.get("image_type", "")),
            platform=str(request.get("platform", "")),
            visual_style=str(request.get("visual_style", "")),
        )

    def build_result(
        self,
        *,
        success: bool,
        prompt: str,
        negative_prompt: str,
        visual_style: str,
        lighting_style: str,
        composition_style: str,
        camera_direction: str,
        aspect_ratio: str,
        platform: str,
        image_type: str,
        metadata: dict[str, Any],
        warnings: list[str],
        errors: list[str],
        cinematic_rules_applied: list[str],
        validation_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a stable engine response."""

        return {
            "success": success,
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "visual_style": visual_style,
            "lighting_style": lighting_style,
            "composition_style": composition_style,
            "camera_direction": camera_direction,
            "aspect_ratio": aspect_ratio,
            "platform": platform,
            "image_type": image_type,
            "metadata": metadata,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
            "cinematic_rules_applied": cinematic_rules_applied,
            "validation": validation_result,
            "request_contract": build_image_prompt_request_contract(),
            "response_contract": build_image_prompt_response_contract(),
        }

    def _build_metadata(self, request: dict[str, Any], style: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
        """Build safe observability metadata."""

        return {
            "brand": request.get("brand", ""),
            "platform": request.get("platform", ""),
            "content_type": "image_prompt",
            "campaign_type": request.get("campaign_type", ""),
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "image_type": request.get("image_type", ""),
            "visual_style": style.get("name", ""),
            "cinematic_rules_count": len(rules.get("rules", [])),
            "negative_prompt_enabled": bool(request.get("enable_negative_prompts", True)),
        }

    def _normalize_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Normalize request values and apply defaults."""

        normalized = dict(request or {})
        normalized["brand"] = normalize_key(str(normalized.get("brand") or ""))
        normalized["platform"] = normalize_key(str(normalized.get("platform") or ""))
        normalized["content_type"] = normalize_key(str(normalized.get("content_type") or "image_prompt"))
        normalized["campaign_type"] = normalize_key(str(normalized.get("campaign_type") or ""))
        normalized["objective"] = str(normalized.get("objective", "")).strip()
        normalized["audience"] = str(normalized.get("audience", "")).strip()
        normalized["location"] = normalize_key(str(normalized.get("location") or ""))
        normalized["property_type"] = normalize_key(str(normalized.get("property_type") or ""))
        normalized["visual_style"] = str(normalized.get("visual_style") or DEFAULT_VISUAL_STYLE).strip()
        normalized["creative_direction"] = str(normalized.get("creative_direction") or "").strip()
        image_type = normalize_image_type(str(normalized.get("image_type") or normalized.get("content_type") or "social_media_visual"))
        if image_type not in get_supported_image_prompt_types():
            image_type = "social_media_visual"
        normalized["image_type"] = image_type
        aspect_ratio = normalize_aspect_ratio(str(normalized.get("aspect_ratio") or "4:5"))
        if aspect_ratio not in get_supported_aspect_ratios():
            aspect_ratio = "4:5"
        normalized["aspect_ratio"] = aspect_ratio
        normalized["extra_notes"] = str(normalized.get("extra_notes") or "").strip()
        normalized["camera_direction"] = str(normalized.get("camera_direction") or DEFAULT_CAMERA_DIRECTION).strip()
        normalized["enable_negative_prompts"] = bool(normalized.get("enable_negative_prompts", True))
        normalized["enable_cinematic_enhancement"] = bool(normalized.get("enable_cinematic_enhancement", True))
        return normalized


if __name__ == "__main__":
    demo_engine = ImagePromptEngine()
    sample_requests = [
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "image_prompt",
            "campaign_type": "property_launch",
            "objective": "generate_leads",
            "audience": "relocation_clients",
            "location": "sant_llorenc_des_cardassar",
            "property_type": "rustic_home",
            "visual_style": "mediterranean_lifestyle",
            "creative_direction": "Rustic exterior with modern comfort inside, close to Manacor and beaches.",
            "image_type": "property_exterior",
            "aspect_ratio": "4:5",
            "extra_notes": "Premium but approachable, realistic, no exaggerated luxury.",
        },
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "image_prompt",
            "campaign_type": "property_launch",
            "objective": "generate_leads",
            "audience": "relocation_clients",
            "location": "palma",
            "property_type": "apartment",
            "visual_style": "premium_interior",
            "creative_direction": "Light-filled interior with premium but believable finishes.",
            "image_type": "property_interior",
            "aspect_ratio": "9:16",
        },
    ]
    for sample in sample_requests:
        result = demo_engine.generate_image_prompt(sample)
        print(result)
