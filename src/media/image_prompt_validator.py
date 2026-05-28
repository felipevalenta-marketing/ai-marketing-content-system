"""Validation for generated image prompt instructions."""

from __future__ import annotations

from typing import Any

from src.governance.governance_rules import get_governance_rules
from src.media.image_prompt_contracts import get_supported_aspect_ratios, get_supported_platforms, get_supported_image_prompt_types
from src.media.visual_styles import list_visual_styles
from src.utils.file_utils import normalize_key


class ImagePromptValidator:
    """Validate prompt quality, realism, and platform fit."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or get_governance_rules()

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate an image prompt result payload."""

        warnings: list[str] = []
        errors: list[str] = []
        scores = {
            "realism": 0.0,
            "completeness": 0.0,
            "brand_fit": 0.0,
            "platform_fit": 0.0,
            "conciseness": 0.0,
        }
        if not isinstance(payload, dict):
            return {"valid": False, "warnings": [], "errors": ["Image prompt payload must be a dictionary."], "scores": scores}

        prompt = str(payload.get("prompt") or payload.get("enhanced_image_prompt") or "").strip()
        negative_prompt = str(payload.get("negative_prompt") or "").strip()
        visual_style = normalize_key(str(payload.get("visual_style") or ""))
        lighting_style = str(payload.get("lighting_style") or "").strip()
        composition_style = str(payload.get("composition_style") or "").strip()
        camera_direction = str(payload.get("camera_direction") or "").strip()
        aspect_ratio = str(payload.get("aspect_ratio") or "").strip()
        platform = normalize_key(str(payload.get("platform") or ""))
        image_type = normalize_key(str(payload.get("image_type") or ""))
        negative_prompt_enabled = bool(payload.get("enable_negative_prompts", True))

        required_fields = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "visual_style": visual_style,
            "lighting_style": lighting_style,
            "composition_style": composition_style,
            "camera_direction": camera_direction,
            "aspect_ratio": aspect_ratio,
        }
        missing = [field for field, value in required_fields.items() if not value]
        if not prompt:
            errors.append("Image prompt is empty.")
        if not negative_prompt and negative_prompt_enabled:
            warnings.append("Negative prompt is missing.")
        if missing:
            warnings.append(f"Image prompt is missing fields: {', '.join(missing)}")
        if len(prompt) > 1200:
            warnings.append("Image prompt may be too long.")
        if not any(term in prompt.lower() for term in ("realistic", "photorealistic", "natural light", "architectural photography")):
            warnings.append("Prompt should reinforce realism and photographic clarity.")

        if aspect_ratio and aspect_ratio not in get_supported_aspect_ratios():
            errors.append(f"Unsupported aspect ratio: {aspect_ratio}")
        if platform and platform not in get_supported_platforms():
            warnings.append(f"Unsupported platform guidance: {platform}")
        if image_type and image_type not in get_supported_image_prompt_types():
            warnings.append(f"Unsupported image type: {image_type}")
        if visual_style and visual_style not in list_visual_styles():
            warnings.append(f"Unsupported visual style: {visual_style}")

        lower_prompt = prompt.lower()
        banned_phrases = self.rules["banned_phrases"] + self.rules["real_estate_safety_rules"]["critical_phrases"]
        risky_phrases = [phrase for phrase in banned_phrases if phrase in lower_prompt]
        if risky_phrases:
            errors.append(f"Forbidden claim language detected: {', '.join(risky_phrases)}")
        if any(term in lower_prompt for term in ("cgi", "fantasy", "impossible", "fake luxury")):
            warnings.append("Prompt may imply unrealistic visuals.")
        if any(term in lower_prompt for term in ("guaranteed roi", "guaranteed return", "risk-free investment")):
            errors.append("Prompt contains unsupported investment claims.")

        scores["realism"] = self._score_realism(prompt)
        scores["completeness"] = self._score_completeness(required_fields)
        scores["brand_fit"] = self._score_brand_fit(prompt)
        scores["platform_fit"] = self._score_platform_fit(platform, aspect_ratio)
        scores["conciseness"] = self._score_conciseness(prompt)

        valid = not errors and scores["completeness"] >= 60 and scores["realism"] >= 60
        return {"valid": valid, "warnings": list(dict.fromkeys(warnings)), "errors": list(dict.fromkeys(errors)), "scores": scores}

    def _score_realism(self, prompt: str) -> float:
        lowered = prompt.lower()
        score = 100.0
        for term in ("cgi", "fantasy", "impossible", "fake luxury", "oversaturated", "unrealistic lighting"):
            if term in lowered:
                score -= 12
        if "natural light" in lowered or "realistic" in lowered or "photorealistic" in lowered:
            score += 5
        return max(0.0, min(100.0, round(score, 2)))

    def _score_completeness(self, fields: dict[str, Any]) -> float:
        present = sum(1 for value in fields.values() if bool(str(value).strip()))
        return round((present / max(1, len(fields))) * 100.0, 2)

    def _score_brand_fit(self, prompt: str) -> float:
        lowered = prompt.lower()
        score = 100.0
        for term in self.rules["brand_tone_signals"]["negative"]:
            if term in lowered:
                score -= 8
        for term in self.rules["brand_tone_signals"]["positive"]:
            if term in lowered:
                score += 2
        return max(0.0, min(100.0, round(score, 2)))

    def _score_platform_fit(self, platform: str, aspect_ratio: str) -> float:
        score = 85.0
        preferred = {
            "instagram": {"4:5", "9:16"},
            "facebook": {"4:5", "1:1"},
            "linkedin": {"16:9", "1:1"},
            "website": {"16:9", "3:2", "4:5"},
            "luxury_listing_portal": {"4:5", "3:2", "16:9"},
        }
        if aspect_ratio and platform in preferred and aspect_ratio not in preferred[platform]:
            score -= 18
        return max(0.0, min(100.0, round(score, 2)))

    def _score_conciseness(self, prompt: str) -> float:
        length = len(prompt)
        if length <= 500:
            return 100.0
        if length <= 800:
            return 85.0
        if length <= 1100:
            return 70.0
        return 50.0
