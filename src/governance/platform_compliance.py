"""Platform-specific compliance checks."""

from __future__ import annotations

from typing import Any

from src.governance.governance_rules import get_governance_rules
from src.output.output_contracts import normalize_output_content_type
from src.adapters.platform_contracts import normalize_platform_name


class PlatformComplianceChecker:
    """Validate that content fits a target platform."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or get_governance_rules()

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return platform compliance diagnostics."""

        platform = normalize_platform_name(str(payload.get("platform", "")))
        content_type = normalize_output_content_type(str(payload.get("content_type", "")))
        output = self._extract_output(payload)
        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}

        if platform not in self.rules["platform_rules"]:
            warnings.append(f"Unsupported platform: {platform}")
            return {"score": 50.0, "warnings": warnings, "errors": errors, "checks": {"unsupported_platform": True}}

        if content_type in {"video_prompt", "video_script"}:
            hook = self._get(output, "hook")
            script = self._get(output, "script", "scene_description")
            voiceover = self._get(output, "voiceover", "voiceover_direction")
            cta = self._get(output, "cta")
            scene_sequence = self._normalize_list(output.get("scene_sequence") or output.get("sequence"))
            storyboard = self._normalize_list(output.get("storyboard"))
            duration = self._get(output, "duration")
            checks.update(
                {
                    "hook_exists": bool(hook),
                    "script_exists": bool(script),
                    "voiceover_exists": bool(voiceover),
                    "cta_exists": bool(cta),
                    "scene_count": len(scene_sequence),
                    "storyboard_count": len(storyboard),
                    "duration": duration,
                }
            )
            if not hook:
                warnings.append("Video script is missing a hook.")
            if not script:
                errors.append("Video script is missing a script body.")
            if not voiceover:
                warnings.append("Video script is missing voiceover direction.")
            if not cta:
                warnings.append("Video script is missing a CTA.")
            if not scene_sequence:
                errors.append("Video script is missing a scene sequence.")
            if not storyboard:
                warnings.append("Video script is missing storyboard detail.")
            if platform in {"instagram", "tiktok"} and len(scene_sequence) > 6:
                warnings.append("Video script has too many scenes for a vertical short-form platform.")
            if platform == "linkedin" and self._is_overly_emotional(script):
                warnings.append("LinkedIn video script appears overly emotional.")
            if platform == "website" and self._has_hype(script):
                warnings.append("Website video script appears exaggerated.")
            score = 100.0
            score -= 10 if not hook else 0
            score -= 15 if not script else 0
            score -= 8 if not voiceover else 0
            score -= 8 if not cta else 0
            score -= 8 if not scene_sequence else 0
            score -= 4 if not storyboard else 0
            if platform in {"instagram", "tiktok"} and duration not in {"15s", "30s", "45s"}:
                score -= 10
            if platform == "linkedin" and self._is_overly_emotional(script):
                score -= 8
            if platform == "website" and self._has_hype(script):
                score -= 8
            return {"score": max(0.0, round(score, 2)), "warnings": warnings, "errors": errors, "checks": checks}

        if platform == "instagram":
            hook = self._get(output, "hook")
            caption = self._get(output, "caption")
            hashtags = self._normalize_list(output.get("hashtags"))
            cta = self._get(output, "cta")
            checks.update({"hook_exists": bool(hook), "caption_exists": bool(caption), "hashtags_count": len(hashtags), "cta_exists": bool(cta)})
            if not hook:
                warnings.append("Instagram output is missing a hook.")
            if not caption:
                errors.append("Instagram output is missing a caption.")
            if len(hashtags) > self.rules["platform_rules"]["instagram"]["max_hashtags"]:
                warnings.append("Instagram hashtags are excessive.")
            if not cta:
                warnings.append("Instagram output is missing a CTA.")
            score = 100.0 - (10 if not hook else 0) - (12 if not caption else 0) - (8 if len(hashtags) > self.rules["platform_rules"]["instagram"]["max_hashtags"] else 0) - (8 if not cta else 0)
            return {"score": max(0.0, round(score, 2)), "warnings": warnings, "errors": errors, "checks": checks}

        if platform == "facebook":
            post = self._get(output, "post") or self._get(output, "caption")
            hashtags = self._normalize_list(output.get("hashtags"))
            cta = self._get(output, "cta")
            checks.update({"post_exists": bool(post), "hashtags_count": len(hashtags), "cta_exists": bool(cta)})
            if not post:
                errors.append("Facebook output is missing a post body.")
            if len(hashtags) > self.rules["platform_rules"]["facebook"]["max_hashtags"]:
                warnings.append("Facebook hashtags are excessive.")
            if not cta:
                warnings.append("Facebook output is missing a CTA.")
            score = 100.0 - (15 if not post else 0) - (5 if len(hashtags) > self.rules["platform_rules"]["facebook"]["max_hashtags"] else 0) - (8 if not cta else 0)
            return {"score": max(0.0, round(score, 2)), "warnings": warnings, "errors": errors, "checks": checks}

        if platform == "linkedin":
            headline = self._get(output, "headline")
            body = self._get(output, "body")
            hashtags = self._normalize_list(output.get("hashtags"))
            cta = self._get(output, "cta")
            checks.update({"headline_exists": bool(headline), "body_exists": bool(body), "hashtags_count": len(hashtags), "cta_exists": bool(cta)})
            if not headline:
                warnings.append("LinkedIn output is missing a headline.")
            if not body:
                errors.append("LinkedIn output is missing a body.")
            if len(hashtags) > self.rules["platform_rules"]["linkedin"]["max_hashtags"]:
                warnings.append("LinkedIn hashtags are excessive.")
            if not cta:
                warnings.append("LinkedIn output is missing a CTA.")
            if self._is_overly_emotional(body):
                warnings.append("LinkedIn copy appears overly emotional.")
            score = 100.0 - (10 if not headline else 0) - (15 if not body else 0) - (5 if len(hashtags) > self.rules["platform_rules"]["linkedin"]["max_hashtags"] else 0) - (6 if self._is_overly_emotional(body) else 0)
            return {"score": max(0.0, round(score, 2)), "warnings": warnings, "errors": errors, "checks": checks}

        if platform == "email":
            subject = self._get(output, "subject")
            preview_text = self._get(output, "preview_text")
            body = self._get(output, "body")
            cta = self._get(output, "cta")
            hashtags = self._normalize_list(output.get("hashtags"))
            checks.update({"subject_exists": bool(subject), "preview_text_exists": bool(preview_text), "body_exists": bool(body), "cta_exists": bool(cta), "hashtags_count": len(hashtags)})
            if not subject:
                errors.append("Email output is missing a subject.")
            if not preview_text:
                errors.append("Email output is missing preview text.")
            if not body:
                errors.append("Email output is missing a body.")
            if not cta:
                warnings.append("Email output is missing a CTA.")
            if hashtags:
                warnings.append("Email should not include hashtags.")
            score = 100.0 - (15 if not subject else 0) - (10 if not preview_text else 0) - (15 if not body else 0) - (8 if hashtags else 0)
            return {"score": max(0.0, round(score, 2)), "warnings": warnings, "errors": errors, "checks": checks}

        if platform == "website_listing":
            title = self._get(output, "title")
            short_description = self._get(output, "short_description")
            long_description = self._get(output, "long_description")
            highlights = self._normalize_list(output.get("highlights"))
            cta = self._get(output, "cta")
            hashtags = self._normalize_list(output.get("hashtags"))
            checks.update({"title_exists": bool(title), "short_description_exists": bool(short_description), "long_description_exists": bool(long_description), "highlights_count": len(highlights), "cta_exists": bool(cta), "hashtags_count": len(hashtags)})
            if not title:
                errors.append("Website listing is missing a title.")
            if not long_description:
                errors.append("Website listing is missing a long description.")
            if not highlights:
                warnings.append("Website listing has no highlights.")
            if hashtags:
                warnings.append("Website listing should not include hashtags.")
            if self._has_hype(long_description):
                warnings.append("Website listing appears exaggerated.")
            score = 100.0 - (15 if not title else 0) - (15 if not long_description else 0) - (6 if not highlights else 0) - (8 if hashtags else 0)
            return {"score": max(0.0, round(score, 2)), "warnings": warnings, "errors": errors, "checks": checks}

        warnings.append(f"Unsupported platform: {platform}")
        return {"score": 50.0, "warnings": warnings, "errors": errors, "checks": {"unsupported_platform": True, "content_type": content_type}}

    def _extract_output(self, payload: dict[str, Any]) -> dict[str, Any]:
        if isinstance(payload.get("formatted_output"), dict):
            return dict(payload["formatted_output"])
        if isinstance(payload.get("platform_variants"), dict):
            platform = payload.get("platform") or next(iter(payload["platform_variants"]), None)
            variant = payload["platform_variants"].get(platform) if platform else None
            if isinstance(variant, dict):
                content = variant.get("content")
                if isinstance(content, dict):
                    return dict(content)
        return dict(payload or {})

    def _get(self, output: dict[str, Any], *keys: str) -> str:
        for key in keys:
            value = output.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _normalize_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return []

    def _is_overly_emotional(self, text: str) -> bool:
        lowered = (text or "").lower()
        return any(term in lowered for term in ("amazing", "incredible", "life-changing", "dreamy", "magical"))

    def _has_hype(self, text: str) -> bool:
        lowered = (text or "").lower()
        return any(term in lowered for term in ("exclusive", "unparalleled", "best", "ultimate", "world-class"))
