"""Map campaign context to visual direction guidance."""

from __future__ import annotations

from typing import Any

from src.creative.color_palette import get_color_palette
from src.creative.moodboard_rules import resolve_moodboard_rules
from src.creative.visual_identity import DEFAULT_VISUAL_IDENTITY, get_visual_identity
from src.utils.file_utils import normalize_key


class BrandVisualMapper:
    """Resolve visual identity, palettes, and downstream guidance."""

    def select_visual_identity(self, request: dict[str, Any]) -> dict[str, Any]:
        """Select the best matching visual identity profile."""

        requested = normalize_key(str(request.get("visual_style") or request.get("visual_identity") or ""))
        campaign_type = normalize_key(str(request.get("campaign_type") or ""))
        audience = normalize_key(str(request.get("audience") or ""))
        property_type = normalize_key(str(request.get("property_type") or ""))
        objective = normalize_key(str(request.get("objective") or ""))

        candidates = [
            requested,
            self._campaign_identity_hint(campaign_type),
            self._audience_identity_hint(audience),
            self._property_identity_hint(property_type),
            self._objective_identity_hint(objective),
            DEFAULT_VISUAL_IDENTITY,
        ]
        for candidate in candidates:
            if candidate:
                profile = get_visual_identity(candidate)
                if profile:
                    return profile
        return get_visual_identity(DEFAULT_VISUAL_IDENTITY)

    def select_moodboard_rules(self, request: dict[str, Any], asset_types: list[str] | None = None) -> list[dict[str, Any]]:
        """Select moodboard rules for the campaign."""

        return resolve_moodboard_rules(
            str(request.get("campaign_type") or ""),
            str(request.get("platforms", [""])[0] if request.get("platforms") else request.get("platform", "")),
            asset_types=asset_types,
        )

    def select_color_palette(self, request: dict[str, Any], visual_identity: dict[str, Any] | None = None) -> dict[str, Any]:
        """Select a descriptive palette from the visual identity."""

        identity = visual_identity or self.select_visual_identity(request)
        palette_name = str(identity.get("color_palette") or request.get("visual_style") or DEFAULT_VISUAL_IDENTITY)
        return get_color_palette(palette_name)

    def select_lighting_direction(self, request: dict[str, Any], visual_identity: dict[str, Any] | None = None) -> str:
        """Select lighting guidance."""

        identity = visual_identity or self.select_visual_identity(request)
        return str(identity.get("lighting") or "Natural daylight with soft, realistic contrast.").strip()

    def select_camera_style(self, request: dict[str, Any], visual_identity: dict[str, Any] | None = None) -> str:
        """Select camera style guidance."""

        identity = visual_identity or self.select_visual_identity(request)
        return str(identity.get("camera_style") or "Steady, composed, and realistic.").strip()

    def select_composition_rules(self, request: dict[str, Any], visual_identity: dict[str, Any] | None = None) -> list[str]:
        """Return concise composition rules."""

        identity = visual_identity or self.select_visual_identity(request)
        rules = [str(identity.get("composition") or "").strip()]
        rules.extend(
            [
                "Maintain real-world scale and believable spatial relationships.",
                "Keep the subject clear and avoid visual clutter.",
            ]
        )
        return [rule for rule in dict.fromkeys(rules) if rule]

    def build_platform_guidelines(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build platform-aware creative guidance."""

        platforms = [normalize_key(platform) for platform in request.get("platforms", [])] or [normalize_key(str(request.get("platform", "")))]
        guidelines: dict[str, Any] = {}
        for platform in platforms:
            if not platform:
                continue
            if platform == "instagram":
                guidelines[platform] = {
                    "tone": "visually emotional, lifestyle-led, warm, and scroll-stopping",
                    "first_frame": "Use a strong first frame with immediate visual context.",
                    "framing": "vertical-first, elegant, and human",
                }
            elif platform == "facebook":
                guidelines[platform] = {
                    "tone": "warmer and more human",
                    "first_frame": "Use approachable community framing.",
                    "framing": "clear, warm, and less editorial",
                }
            elif platform == "linkedin":
                guidelines[platform] = {
                    "tone": "professional, polished, and market-aware",
                    "first_frame": "Use architecture or market insight first.",
                    "framing": "less emotional and more authoritative",
                }
            elif platform == "email":
                guidelines[platform] = {
                    "tone": "clean and supportive",
                    "first_frame": "Use a clear hero image with minimal clutter.",
                    "framing": "simple, direct, and CTA-supportive",
                }
            elif platform == "website":
                guidelines[platform] = {
                    "tone": "factual and polished",
                    "first_frame": "Use property-first clarity.",
                    "framing": "listing-ready and realistic",
                }
        return guidelines

    def build_media_guidelines(self, request: dict[str, Any], visual_identity: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build media-specific guidance for downstream modules."""

        identity = visual_identity or self.select_visual_identity(request)
        palette = self.select_color_palette(request, identity)
        moodboard_rules = self.select_moodboard_rules(request, asset_types=request.get("assets_required", []))
        return {
            "image_prompts": {
                "lighting": str(identity.get("lighting") or ""),
                "lens": "natural perspective and realistic architectural photography",
                "composition": str(identity.get("composition") or ""),
                "style": str(identity.get("mood") or ""),
                "negative_prompt": "Avoid fake luxury, impossible architecture, unrealistic lighting, and CGI look.",
                "realism_constraints": ["No invented features", "No fake views", "No exaggerated scale"],
            },
            "video_scripts": {
                "mood": str(identity.get("mood") or ""),
                "pacing": "concise, platform-aware, and visually structured",
                "camera_style": str(identity.get("camera_style") or ""),
                "scene_progression": "hook, context, value, relevance, CTA",
                "music_direction": "premium but restrained",
                "first_frame_strategy": "show the strongest visual immediately",
            },
            "campaign_assets": {
                "palette": palette.get("name", ""),
                "moodboard_rules": [rule.get("name", "") for rule in moodboard_rules],
                "consistency": "reuse the same palette, tone, and framing across assets",
                "cta_tone": "soft, clear, and brand-safe",
            },
        }

    def build_asset_guidelines(self, request: dict[str, Any], visual_identity: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build asset-specific creative guidance."""

        identity = visual_identity or self.select_visual_identity(request)
        palette = self.select_color_palette(request, identity)
        return {
            "visual_identity": identity.get("name", ""),
            "palette": palette.get("name", ""),
            "lighting": identity.get("lighting", ""),
            "camera_style": identity.get("camera_style", ""),
            "composition": identity.get("composition", ""),
            "notes": [
                "Keep image and video assets visually consistent.",
                "Preserve premium but approachable tone.",
                "Avoid fake luxury or impossible visual promises.",
            ],
        }

    def _campaign_identity_hint(self, campaign_type: str) -> str:
        mapping = {
            "property_launch": "mediterranean_luxury",
            "relocation_campaign": "relocation_warmth",
            "neighborhood_spotlight": "natural_mallorca_lifestyle",
            "reform_opportunity": "rustic_modern_comfort",
            "lifestyle_campaign": "natural_mallorca_lifestyle",
            "luxury_listing": "mediterranean_luxury",
            "brand_awareness": "editorial_real_estate",
            "paid_ads": "investment_confidence",
            "seasonal_campaign": "coastal_refined",
        }
        return mapping.get(campaign_type, "")

    def _audience_identity_hint(self, audience: str) -> str:
        if "relocation" in audience:
            return "relocation_warmth"
        if "investment" in audience:
            return "investment_confidence"
        return ""

    def _property_identity_hint(self, property_type: str) -> str:
        if "rustic" in property_type or "reform" in property_type:
            return "rustic_modern_comfort"
        if "coastal" in property_type or "beach" in property_type:
            return "coastal_refined"
        return ""

    def _objective_identity_hint(self, objective: str) -> str:
        if objective in {"generate_leads", "lead_generation"}:
            return "premium_approachable"
        if objective in {"brand_awareness"}:
            return "editorial_real_estate"
        return ""
