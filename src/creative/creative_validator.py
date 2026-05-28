"""Validation for creative direction guidance."""

from __future__ import annotations

from typing import Any

from src.creative.visual_identity import list_visual_identities
from src.governance.governance_rules import get_governance_rules
from src.utils.file_utils import normalize_key


class CreativeDirectionValidator:
    """Validate visual identity, platform fit, and realism."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or get_governance_rules()

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate creative direction guidance."""

        warnings: list[str] = []
        errors: list[str] = []
        scores = {
            "brand_fit": 0.0,
            "visual_consistency": 0.0,
            "platform_fit": 0.0,
            "realism": 0.0,
            "completeness": 0.0,
        }
        if not isinstance(payload, dict):
            return {"valid": False, "warnings": [], "errors": ["Creative direction payload must be a dictionary."], "scores": scores}

        visual_identity = self._safe_dict(payload.get("visual_identity"))
        moodboard = self._safe_dict(payload.get("moodboard"))
        color_palette = self._safe_dict(payload.get("color_palette"))
        lighting_direction = str(payload.get("lighting_direction") or "").strip()
        camera_style = str(payload.get("camera_style") or "").strip()
        platform_guidelines = self._safe_dict(payload.get("platform_guidelines"))
        media_guidelines = self._safe_dict(payload.get("media_guidelines"))
        creative_direction = str(payload.get("creative_direction") or "").strip().lower()
        visual_identity_name = normalize_key(str(visual_identity.get("name") or payload.get("visual_identity_used") or ""))

        if not visual_identity:
            errors.append("Visual identity is missing.")
        if not moodboard:
            warnings.append("Moodboard guidance is missing.")
        if not color_palette:
            warnings.append("Color palette is missing.")
        if not lighting_direction:
            warnings.append("Lighting direction is missing.")
        if not camera_style:
            warnings.append("Camera style is missing.")
        if not platform_guidelines:
            warnings.append("Platform guidelines are missing.")
        if not media_guidelines:
            warnings.append("Media guidelines are missing.")

        if visual_identity_name and visual_identity_name not in list_visual_identities():
            warnings.append(f"Unsupported visual identity: {visual_identity_name}")

        if any(term in creative_direction for term in ("fake luxury", "impossible architecture", "unrealistic", "fake view")):
            errors.append("Creative direction contains unrealistic visual claims.")
        if any(term in creative_direction for term in ("guaranteed roi", "fake scarcity", "fake urgency", "invented location")):
            errors.append("Creative direction contains unsafe marketing claims.")

        scores["brand_fit"] = self._score_brand_fit(visual_identity_name, moodboard, color_palette)
        scores["visual_consistency"] = self._score_consistency(visual_identity, moodboard, color_palette)
        scores["platform_fit"] = self._score_platform_fit(platform_guidelines)
        scores["realism"] = self._score_realism(creative_direction, lighting_direction, camera_style)
        scores["completeness"] = self._score_completeness(visual_identity, moodboard, color_palette, lighting_direction, camera_style, platform_guidelines, media_guidelines)

        valid = not errors and scores["realism"] >= 60 and scores["completeness"] >= 60
        return {
            "valid": valid,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
            "scores": scores,
        }

    def _safe_dict(self, value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, dict) else {}

    def _score_brand_fit(self, visual_identity_name: str, moodboard: dict[str, Any], color_palette: dict[str, Any]) -> float:
        score = 100.0
        if not visual_identity_name:
            score -= 20
        if not moodboard:
            score -= 10
        if not color_palette:
            score -= 10
        return max(0.0, round(score, 2))

    def _score_consistency(self, visual_identity: dict[str, Any], moodboard: dict[str, Any], color_palette: dict[str, Any]) -> float:
        score = 100.0
        if not visual_identity.get("mood"):
            score -= 12
        if not visual_identity.get("lighting"):
            score -= 12
        if not moodboard:
            score -= 10
        if not color_palette.get("primary_colors"):
            score -= 10
        return max(0.0, round(score, 2))

    def _score_platform_fit(self, platform_guidelines: dict[str, Any]) -> float:
        score = 100.0 if platform_guidelines else 55.0
        return max(0.0, round(score, 2))

    def _score_realism(self, creative_direction: str, lighting_direction: str, camera_style: str) -> float:
        score = 100.0
        if any(term in creative_direction for term in ("fake luxury", "impossible architecture", "fantasy", "cgi")):
            score -= 40
        if any(term in creative_direction for term in ("unrealistic", "fake view", "invented", "exaggerated")):
            score -= 20
        if not lighting_direction or not camera_style:
            score -= 20
        return max(0.0, round(score, 2))

    def _score_completeness(
        self,
        visual_identity: dict[str, Any],
        moodboard: dict[str, Any],
        color_palette: dict[str, Any],
        lighting_direction: str,
        camera_style: str,
        platform_guidelines: dict[str, Any],
        media_guidelines: dict[str, Any],
    ) -> float:
        score = 0.0
        for value in (
            visual_identity,
            moodboard,
            color_palette,
            lighting_direction,
            camera_style,
            platform_guidelines,
            media_guidelines,
        ):
            score += 100.0 / 7.0 if value else 0.0
        return round(min(100.0, score), 2)
