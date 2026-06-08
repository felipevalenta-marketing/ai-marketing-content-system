"""Validation helpers for structured video scripts."""

from __future__ import annotations

from typing import Any
import re

from src.media.video_script_contracts import get_supported_durations, get_supported_platforms, get_supported_video_types
from src.utils.file_utils import normalize_key


class VideoScriptValidator:
    """Validate script completeness, pacing, and factual safety."""

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate a generated video script payload."""

        warnings: list[str] = []
        errors: list[str] = []
        scores = {
            "structure": 0.0,
            "pacing": 0.0,
            "brand_fit": 0.0,
            "platform_fit": 0.0,
            "factual_safety": 0.0,
        }
        if not isinstance(payload, dict):
            return {"valid": False, "warnings": [], "errors": ["Video script payload must be a dictionary."], "scores": scores}

        hook = str(payload.get("hook") or "").strip()
        voiceover = str(payload.get("voiceover") or "").strip()
        cta = str(payload.get("cta") or "").strip()
        platform = normalize_key(str(payload.get("platform") or ""))
        video_type = normalize_key(str(payload.get("video_type") or ""))
        duration = str(payload.get("duration") or "").strip().lower()
        scene_1 = str(payload.get("scene_1") or "").strip()
        scene_2 = str(payload.get("scene_2") or "").strip()
        scene_3 = str(payload.get("scene_3") or "").strip()
        legacy_script = str(payload.get("script") or "").strip()
        scene_sequence = payload.get("scene_sequence")
        storyboard = payload.get("storyboard")

        if not hook:
            warnings.append("Video script is missing a hook.")
        if not any([scene_1, scene_2, scene_3]) and not legacy_script and not isinstance(scene_sequence, list):
            errors.append("Video script is empty.")
        if not scene_1:
            warnings.append("Video script is missing scene_1.")
        if not scene_2:
            warnings.append("Video script is missing scene_2.")
        if not scene_3:
            warnings.append("Video script is missing scene_3.")
        if not voiceover:
            warnings.append("Video script is missing a voiceover structure.")
        if not cta:
            warnings.append("Video script is missing a CTA.")

        if duration and duration not in get_supported_durations():
            errors.append(f"Unsupported duration: {duration}")
        if video_type and video_type not in get_supported_video_types():
            warnings.append(f"Unsupported video type: {video_type}")
        if platform and platform not in get_supported_platforms():
            warnings.append(f"Unsupported platform: {platform}")

        lower = " ".join([hook, scene_1, scene_2, scene_3, voiceover, cta, legacy_script]).lower()
        if any(term in lower for term in ("guaranteed roi", "guaranteed return", "risk-free investment")):
            errors.append("Video script contains unsupported investment claims.")
        if any(term in lower for term in ("limited time only", "act now", "hurry", "don't miss", "fake scarcity", "fake urgency")):
            warnings.append("Video script contains urgency language that should be reviewed.")
        if any(term in lower for term in ("exclusive opportunity", "unbeatable price", "best investment")):
            warnings.append("Video script contains unsupported exclusivity or hype language.")
        if self._detect_invented_claims(lower):
            errors.append("Video script may invent property facts.")

        structure_score = self._score_structure(hook, scene_1, scene_2, scene_3, voiceover, cta, scene_sequence, storyboard)
        pacing_score = self._score_pacing(duration, scene_sequence, voiceover)
        brand_fit_score = self._score_brand_fit(lower)
        platform_fit_score = self._score_platform_fit(platform, duration, video_type, scene_sequence)
        factual_score = self._score_factual_safety(lower)

        valid = not errors and structure_score >= 60 and factual_score >= 60
        return {
            "valid": valid,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
            "scores": {
                "structure": structure_score,
                "pacing": pacing_score,
                "brand_fit": brand_fit_score,
                "platform_fit": platform_fit_score,
                "factual_safety": factual_score,
            },
        }

    def _score_structure(self, hook: str, scene_1: str, scene_2: str, scene_3: str, voiceover: str, cta: str, scene_sequence: Any, storyboard: Any) -> float:
        fields = [hook, scene_1, scene_2, scene_3, voiceover, cta]
        non_empty = sum(1 for value in fields if bool(value.strip()))
        if isinstance(scene_sequence, list) and len(scene_sequence) >= 3:
            non_empty += 1
        if isinstance(storyboard, list) and storyboard:
            non_empty += 1
        return round(min(100.0, (non_empty / 7.0) * 100.0), 2)

    def _score_pacing(self, duration: str, scene_sequence: Any, voiceover: str) -> float:
        scene_count = len(scene_sequence) if isinstance(scene_sequence, list) else 0
        duration_map = {"15s": 3, "30s": 5, "45s": 5, "60s": 6, "90s": 7}
        expected = duration_map.get(duration, 5)
        score = 100.0
        if scene_count and abs(scene_count - expected) > 1:
            score -= 18
        if len(voiceover.split()) > self._max_words_for_duration(duration):
            score -= 14
        return max(0.0, round(score, 2))

    def _score_brand_fit(self, text: str) -> float:
        score = 100.0
        for term in ("hype", "cheap", "ultra luxury", "world class", "best investment"):
            if term in text:
                score -= 8
        if "premium" in text or "approachable" in text:
            score += 2
        return max(0.0, min(100.0, round(score, 2)))

    def _score_platform_fit(self, platform: str, duration: str, video_type: str, scene_sequence: Any) -> float:
        score = 85.0
        preferred = {
            "instagram": {"15s", "30s", "45s"},
            "tiktok": {"15s", "30s"},
            "facebook": {"30s", "45s", "60s"},
            "youtube": {"30s", "45s", "60s", "90s"},
            "website": {"30s", "45s", "60s"},
            "linkedin": {"30s", "45s", "60s"},
        }
        if platform in preferred and duration and duration not in preferred[platform]:
            score -= 16
        if platform in {"instagram", "tiktok"} and isinstance(scene_sequence, list) and len(scene_sequence) > 6:
            score -= 10
        if video_type == "brand_story_video" and platform in {"instagram", "tiktok"}:
            score -= 4
        return max(0.0, min(100.0, round(score, 2)))

    def _score_factual_safety(self, text: str) -> float:
        score = 100.0
        if any(term in text for term in ("guaranteed roi", "guaranteed return", "risk-free investment")):
            score -= 40
        if any(term in text for term in ("fake scarcity", "fake urgency", "limited time only", "act now")):
            score -= 14
        if any(term in text for term in ("private beach", "direct beach access", "unbeatable price", "best investment")):
            score -= 18
        return max(0.0, round(score, 2))

    def _max_words_for_duration(self, duration: str) -> int:
        mapping = {"15s": 34, "30s": 68, "45s": 96, "60s": 120, "90s": 170}
        return mapping.get(duration, 68)

    def _detect_invented_claims(self, text: str) -> bool:
        return any(term in text for term in ("invented", "impossible", "fantasy", "fake location", "fake amenity"))
