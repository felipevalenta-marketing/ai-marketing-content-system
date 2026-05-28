"""Creative direction orchestration engine."""

from __future__ import annotations

from typing import Any

from src.creative.brand_visual_mapper import BrandVisualMapper
from src.creative.creative_contracts import (
    build_creative_direction_request_contract,
    build_creative_direction_response_contract,
    get_supported_creative_direction_types,
    get_supported_platforms,
    normalize_creative_direction_type,
)
from src.creative.creative_result import build_creative_direction_failure, build_creative_direction_success
from src.creative.creative_validator import CreativeDirectionValidator
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context


class CreativeDirectionEngine:
    """Create structured creative direction and visual identity guidance."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.mapper = BrandVisualMapper()
        self.validator = CreativeDirectionValidator()

    def generate_creative_direction(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate a deterministic creative direction payload."""

        valid, reason = self.validate_request(request)
        normalized = self._normalize_request(request)
        log_context(self.logger, f"Generating creative direction for {normalized['brand']}/{normalized['campaign_type']}")
        warnings: list[str] = []
        errors: list[str] = []

        visual_identity = self.build_visual_identity(normalized)
        moodboard = self.build_moodboard(normalized)
        color_palette = self.build_color_palette(normalized)
        lighting_direction = self.build_lighting_direction(normalized)
        camera_style = self.build_camera_style(normalized)
        composition_rules = self.build_composition_rules(normalized)
        platform_guidelines = self.build_platform_guidelines(normalized)
        media_guidelines = self.build_media_guidelines(normalized)
        asset_guidelines = self.mapper.build_asset_guidelines(normalized, visual_identity)
        creative_direction_type = self._resolve_direction_type(normalized)
        governance_notes = self._build_governance_notes(normalized, visual_identity, moodboard, color_palette)

        if not valid and reason:
            warnings.append(reason)

        validation_payload = {
            "creative_direction_type": creative_direction_type,
            "brand": normalized["brand"],
            "campaign_type": normalized["campaign_type"],
            "visual_identity": visual_identity,
            "moodboard": moodboard,
            "color_palette": color_palette,
            "lighting_direction": lighting_direction,
            "camera_style": camera_style,
            "composition_rules": composition_rules,
            "platform_guidelines": platform_guidelines,
            "media_guidelines": media_guidelines,
            "creative_direction": normalized.get("creative_direction", ""),
            "metadata": self._build_metadata(normalized, visual_identity, moodboard, color_palette),
        }
        validation_result = self.validator.validate(validation_payload)
        warnings.extend(validation_result.get("warnings", []))
        errors.extend(validation_result.get("errors", []))

        if errors:
            return build_creative_direction_failure(
                creative_direction_type=creative_direction_type,
                brand=normalized["brand"],
                campaign_type=normalized["campaign_type"],
                metadata=self._build_metadata(normalized, visual_identity, moodboard, color_palette),
                warnings=warnings,
                errors=errors,
                validation=validation_result,
            )

        return build_creative_direction_success(
            creative_direction_type=creative_direction_type,
            brand=normalized["brand"],
            campaign_type=normalized["campaign_type"],
            visual_identity=visual_identity,
            moodboard=moodboard,
            color_palette=color_palette,
            lighting_direction=lighting_direction,
            camera_style=camera_style,
            composition_rules=composition_rules,
            platform_guidelines=platform_guidelines,
            media_guidelines=media_guidelines,
            asset_guidelines=asset_guidelines,
            governance_notes=governance_notes,
            metadata=self._build_metadata(normalized, visual_identity, moodboard, color_palette),
            warnings=warnings,
            errors=errors,
            validation=validation_result,
        )

    def validate_request(self, request: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate creative direction inputs."""

        if not isinstance(request, dict):
            return False, "Creative direction request must be a dictionary."
        brand = normalize_key(str(request.get("brand", "")))
        campaign_type = normalize_key(str(request.get("campaign_type", "")))
        objective = str(request.get("objective", "")).strip()
        audience = str(request.get("audience", "")).strip()
        platforms = [normalize_key(platform) for platform in request.get("platforms", []) if str(platform).strip()]
        if not brand:
            return False, "Missing brand."
        if not campaign_type:
            return False, "Missing campaign_type."
        if not objective:
            return False, "Missing objective."
        if not audience:
            return False, "Missing audience."
        unsupported_platforms = [platform for platform in platforms if platform not in get_supported_platforms()]
        if unsupported_platforms:
            return False, f"Unsupported platform: {', '.join(sorted(set(unsupported_platforms)))}"
        warnings: list[str] = []
        direction_type = self._resolve_direction_type(request)
        if direction_type not in get_supported_creative_direction_types():
            warnings.append(f"Unsupported creative direction type: {direction_type}; using a generic campaign visual direction.")
        if not str(request.get("visual_style", "")).strip():
            warnings.append("Missing visual_style; using a default visual identity.")
        return True, "; ".join(warnings) if warnings else None

    def build_visual_identity(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build the core visual identity profile."""

        return self.mapper.select_visual_identity(request)

    def build_moodboard(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build a moodboard summary."""

        visual_identity = self.build_visual_identity(request)
        rules = self.mapper.select_moodboard_rules(request, asset_types=request.get("assets_required", []))
        return {
            "name": f"{visual_identity.get('name', '')}_moodboard",
            "rules": rules,
            "rule_names": [rule.get("name", "") for rule in rules],
            "mood": visual_identity.get("mood", ""),
            "texture": visual_identity.get("texture", ""),
            "notes": [
                "Stay grounded in Mallorca reality.",
                "Use warm, natural, and premium but approachable visuals.",
            ],
        }

    def build_color_palette(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build the preferred descriptive palette."""

        visual_identity = self.build_visual_identity(request)
        return self.mapper.select_color_palette(request, visual_identity)

    def build_lighting_direction(self, request: dict[str, Any]) -> str:
        """Build lighting direction guidance."""

        visual_identity = self.build_visual_identity(request)
        return self.mapper.select_lighting_direction(request, visual_identity)

    def build_camera_style(self, request: dict[str, Any]) -> str:
        """Build camera style guidance."""

        visual_identity = self.build_visual_identity(request)
        return self.mapper.select_camera_style(request, visual_identity)

    def build_composition_rules(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        """Build a list of composition rules."""

        visual_identity = self.build_visual_identity(request)
        rule_names = self.mapper.select_composition_rules(request, visual_identity)
        return [
            {
                "rule_number": index,
                "name": rule_name or f"rule_{index}",
                "description": rule_name,
                "priority": "high" if index == 1 else "medium",
            }
            for index, rule_name in enumerate(rule_names, start=1)
        ]

    def build_platform_guidelines(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build platform-aware creative guidance."""

        return self.mapper.build_platform_guidelines(request)

    def build_media_guidelines(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build media-specific guidance."""

        visual_identity = self.build_visual_identity(request)
        return self.mapper.build_media_guidelines(request, visual_identity)

    def build_result(
        self,
        *,
        success: bool,
        creative_direction_type: str,
        brand: str,
        campaign_type: str,
        visual_identity: dict[str, Any],
        moodboard: dict[str, Any],
        color_palette: dict[str, Any],
        lighting_direction: str,
        camera_style: str,
        composition_rules: list[dict[str, Any]],
        platform_guidelines: dict[str, Any],
        media_guidelines: dict[str, Any],
        asset_guidelines: dict[str, Any],
        governance_notes: list[str],
        metadata: dict[str, Any],
        warnings: list[str],
        errors: list[str],
        validation_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Return a stable result payload."""

        return {
            "success": success,
            "creative_direction_type": creative_direction_type,
            "brand": brand,
            "campaign_type": campaign_type,
            "visual_identity": visual_identity,
            "moodboard": moodboard,
            "color_palette": color_palette,
            "lighting_direction": lighting_direction,
            "camera_style": camera_style,
            "composition_rules": composition_rules,
            "platform_guidelines": platform_guidelines,
            "media_guidelines": media_guidelines,
            "asset_guidelines": asset_guidelines,
            "governance_notes": governance_notes,
            "metadata": metadata,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
            "validation": validation_result,
            "request_contract": build_creative_direction_request_contract(),
            "response_contract": build_creative_direction_response_contract(),
        }

    def _resolve_direction_type(self, request: dict[str, Any]) -> str:
        campaign_type = normalize_key(str(request.get("campaign_type") or ""))
        mapping = {
            "property_launch": "property_launch_direction",
            "relocation_campaign": "relocation_campaign_direction",
            "neighborhood_spotlight": "neighborhood_spotlight_direction",
            "reform_opportunity": "reform_opportunity_direction",
            "lifestyle_campaign": "lifestyle_campaign_direction",
            "luxury_listing": "luxury_listing_direction",
            "brand_awareness": "brand_awareness_direction",
            "paid_ads": "paid_ads_direction",
            "landing_page": "landing_page_direction",
            "social_campaign": "social_campaign_direction",
            "video_campaign": "video_campaign_direction",
            "editorial_campaign": "editorial_campaign_direction",
            "seasonal_campaign": "seasonal_campaign_direction",
        }
        return mapping.get(campaign_type, "campaign_visual_direction")

    def _build_governance_notes(self, request: dict[str, Any], visual_identity: dict[str, Any], moodboard: dict[str, Any], color_palette: dict[str, Any]) -> list[str]:
        notes = [
            "Avoid fake luxury and unrealistic visual promises.",
            "Keep visual claims grounded in real architecture and lifestyle.",
            "Maintain brand consistency across image, video, and campaign assets.",
        ]
        if visual_identity.get("mood"):
            notes.append(f"Mood: {visual_identity['mood']}.")
        if moodboard.get("rule_names"):
            notes.append("Moodboard rules: " + ", ".join(moodboard["rule_names"]))
        if color_palette.get("name"):
            notes.append(f"Palette: {color_palette['name']}.")
        return notes

    def _normalize_request(self, request: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(request or {})
        normalized["brand"] = normalize_key(str(normalized.get("brand") or ""))
        normalized["campaign_type"] = normalize_key(str(normalized.get("campaign_type") or ""))
        normalized["objective"] = str(normalized.get("objective") or "").strip()
        normalized["audience"] = str(normalized.get("audience") or "").strip()
        normalized["location"] = normalize_key(str(normalized.get("location") or ""))
        normalized["property_type"] = normalize_key(str(normalized.get("property_type") or ""))
        normalized["visual_style"] = str(normalized.get("visual_style") or "").strip()
        normalized["tone"] = str(normalized.get("tone") or "").strip()
        normalized["creative_direction"] = str(normalized.get("creative_direction") or "").strip()
        normalized["extra_notes"] = str(normalized.get("extra_notes") or "").strip()
        normalized["platforms"] = [normalize_key(platform) for platform in normalized.get("platforms", []) if str(platform).strip()]
        normalized["creative_direction_type"] = normalize_creative_direction_type(str(normalized.get("creative_direction_type") or self._resolve_direction_type(normalized)))
        return normalized

    def _build_metadata(self, request: dict[str, Any], visual_identity: dict[str, Any], moodboard: dict[str, Any], color_palette: dict[str, Any]) -> dict[str, Any]:
        return {
            "brand": request.get("brand", ""),
            "campaign_type": request.get("campaign_type", ""),
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "platforms": request.get("platforms", []),
            "visual_style": request.get("visual_style", ""),
            "tone": request.get("tone", ""),
            "creative_direction": request.get("creative_direction", ""),
            "creative_direction_type": request.get("creative_direction_type", ""),
            "visual_identity_used": visual_identity.get("name", ""),
            "moodboard_rule_count": len(moodboard.get("rules", [])),
            "color_palette_used": color_palette.get("name", ""),
        }


if __name__ == "__main__":
    engine = CreativeDirectionEngine()
    sample_request = {
        "brand": "wenzel_partner",
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "platforms": ["instagram", "facebook", "linkedin", "email"],
        "visual_style": "mediterranean_lifestyle",
        "tone": "premium but approachable",
        "creative_direction": "Rustic exterior with modern comfort inside, close to Manacor and beaches.",
        "extra_notes": "Keep visuals realistic, warm, and grounded in Mallorca lifestyle.",
    }
    print(engine.generate_creative_direction(sample_request))
