"""Governance orchestrator for content approval and review."""

from __future__ import annotations

from typing import Any

from src.governance.brand_compliance import BrandComplianceChecker
from src.governance.factual_safety import FactualSafetyChecker
from src.governance.governance_result import build_governance_failure, build_governance_success
from src.governance.governance_rules import get_governance_rules
from src.governance.platform_compliance import PlatformComplianceChecker
from src.governance.quality_scoring import QualityScorer
from src.tracking.token_validator import TokenValidator
from src.creative.creative_validator import CreativeDirectionValidator
from src.media.image_prompt_validator import ImagePromptValidator
from src.media.video_script_validator import VideoScriptValidator
from src.utils.logger import get_logger, log_context, log_warning


class ContentGovernanceEngine:
    """Evaluate content for quality, compliance, and factual safety."""

    def __init__(self, rules: dict[str, Any] | None = None, logger: Any | None = None) -> None:
        self.rules = rules or get_governance_rules()
        self.logger = logger or get_logger(self.__class__.__name__)
        self.quality_scorer = QualityScorer(self.rules)
        self.brand_checker = BrandComplianceChecker(self.rules)
        self.platform_checker = PlatformComplianceChecker(self.rules)
        self.factual_safety_checker = FactualSafetyChecker(self.rules)
        self.token_validator = TokenValidator()
        self.creative_direction_validator = CreativeDirectionValidator(self.rules)
        self.image_prompt_validator = ImagePromptValidator(self.rules)
        self.video_script_validator = VideoScriptValidator()

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate a payload and return a governance decision."""

        if not isinstance(payload, dict):
            return build_governance_failure(
                status="rejected",
                warnings=[],
                errors=["Payload must be a dictionary."],
                recommendations=[],
                checks={},
                metadata={},
            )

        log_context(self.logger, "Evaluating content governance")
        content_type = str(payload.get("content_type", "")).strip().lower()
        if content_type == "creative_direction" or payload.get("creative_direction_result"):
            return self._merge_token_analysis(self._evaluate_creative_direction(payload), self._evaluate_token_usage(payload))
        if content_type == "image_prompt" or payload.get("image_prompt_result"):
            return self._merge_token_analysis(self._evaluate_image_prompt(payload), self._evaluate_token_usage(payload))
        if content_type == "video_script" or payload.get("video_script_result"):
            return self._merge_token_analysis(self._evaluate_video_script(payload), self._evaluate_token_usage(payload))

        formatted_result = self.evaluate_formatted_output(payload)
        platform_result = self.evaluate_platform_variants(payload)
        quality_result = self.quality_scorer.score(payload)
        brand_result = self.brand_checker.check(payload)
        factual_result = self.factual_safety_checker.check(payload)

        scores = {
            "quality_score": quality_result["score"],
            "brand_score": brand_result["score"],
            "platform_score": platform_result["score"],
            "factual_safety_score": factual_result["score"],
        }
        token_result = self._evaluate_token_usage(payload)
        warnings = list(dict.fromkeys(
            quality_result["warnings"]
            + brand_result["warnings"]
            + platform_result["warnings"]
            + factual_result["warnings"]
            + formatted_result.get("warnings", [])
            + token_result.get("warnings", [])
        ))
        errors = list(dict.fromkeys(
            quality_result["errors"]
            + brand_result["errors"]
            + platform_result["errors"]
            + factual_result["errors"]
            + token_result.get("errors", [])
        ))
        checks = {
            "quality": quality_result["checks"],
            "brand": brand_result["checks"],
            "platform": platform_result["checks"],
            "factual_safety": factual_result["checks"],
            "formatted_output": formatted_result.get("checks", {}),
            "token_tracking": token_result.get("checks", {}),
        }
        recommendations = self._build_recommendations(quality_result, brand_result, platform_result, factual_result)
        return self.build_final_decision(scores=scores, warnings=warnings, errors=errors, checks=checks, recommendations=recommendations, payload=payload)

    def evaluate_formatted_output(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate the formatted output only."""

        output = payload.get("formatted_output")
        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}
        if not isinstance(output, dict):
            warnings.append("Formatted output missing or malformed.")
            return {"score": 0.0, "warnings": warnings, "errors": errors, "checks": checks}
        required_fields = [key for key, value in output.items() if isinstance(value, (str, list, dict))]
        checks["field_count"] = len(required_fields)
        checks["has_content"] = any(self._is_non_empty(output.get(field)) for field in required_fields)
        score = 100.0 if checks["has_content"] else 0.0
        return {"score": score, "warnings": warnings, "errors": errors, "checks": checks}

    def evaluate_platform_variants(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate platform variants when available."""

        variants = payload.get("platform_variants")
        if not isinstance(variants, dict) or not variants:
            output = payload.get("formatted_output") or {}
            if isinstance(output, dict):
                text = self._serialize_content(output)
                score = 100.0 if text.strip() else 0.0
                warnings = [] if text.strip() else ["No platform variants available."]
                return {"score": score, "warnings": warnings, "errors": [], "checks": {"variant_count": 0}}
            return {"score": 0.0, "warnings": ["No platform variants available."], "errors": [], "checks": {"variant_count": 0}}

        platform_scores: list[float] = []
        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {"variant_count": len(variants), "platforms": sorted(variants.keys())}

        for platform, variant_payload in variants.items():
            variant_content = {}
            if isinstance(variant_payload, dict):
                content = variant_payload.get("content")
                if isinstance(content, dict):
                    variant_content = content
                else:
                    variant_content = variant_payload
            result = self.platform_checker.check({
                "platform": platform,
                "content_type": payload.get("content_type", ""),
                **variant_content,
                "metadata": payload.get("metadata", {}),
            })
            platform_scores.append(result["score"])
            warnings.extend(result["warnings"])
            errors.extend(result["errors"])
            checks[platform] = result["checks"]

        score = sum(platform_scores) / len(platform_scores) if platform_scores else 0.0
        return {"score": round(score, 2), "warnings": list(dict.fromkeys(warnings)), "errors": list(dict.fromkeys(errors)), "checks": checks}

    def build_final_decision(
        self,
        scores: dict[str, float],
        warnings: list[str],
        errors: list[str],
        checks: dict[str, Any],
        recommendations: list[str],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Combine scores into a final governance decision."""

        quality = float(scores.get("quality_score", 0.0))
        brand = float(scores.get("brand_score", 0.0))
        platform = float(scores.get("platform_score", 0.0))
        factual = float(scores.get("factual_safety_score", 0.0))
        overall = round((quality * 0.30) + (brand * 0.25) + (platform * 0.20) + (factual * 0.25), 2)

        status = "needs_review"
        approved = False
        critical_safety_error = any(self._is_critical_safety_error(error) for error in errors)
        thresholds = self.rules["score_thresholds"]

        if critical_safety_error:
            status = "rejected"
        elif overall >= thresholds["approved"] and not errors:
            status = "approved"
            approved = True
        elif overall >= thresholds["approved_with_warnings"] and not errors:
            status = "approved_with_warnings"
            approved = True
        elif overall >= thresholds["needs_review"] or len(warnings) >= 3:
            status = "needs_review"
        else:
            status = "rejected" if errors else "needs_review"

        metadata = {
            "brand": payload.get("metadata", {}).get("brand") or payload.get("brand", ""),
            "platform": payload.get("platform", ""),
            "content_type": payload.get("content_type", ""),
            "objective": payload.get("metadata", {}).get("objective") or payload.get("objective", ""),
            "audience": payload.get("metadata", {}).get("audience") or payload.get("audience", ""),
            "location": payload.get("metadata", {}).get("location") or payload.get("location", ""),
            "decision_basis": "weighted governance score",
        }
        return build_governance_success(
            approved=approved,
            status=status,
            quality_score=quality,
            brand_score=brand,
            platform_score=platform,
            factual_safety_score=factual,
            overall_score=overall,
            warnings=warnings,
            errors=errors,
            recommendations=recommendations,
            checks=checks,
            metadata=metadata,
        )

    def _evaluate_image_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate image prompt results with prompt-specific safety checks."""

        image_result = payload.get("image_prompt_result")
        if not isinstance(image_result, dict) or not image_result:
            image_result = {
                "image_prompt": payload.get("formatted_output", {}).get("image_prompt", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "prompt": payload.get("formatted_output", {}).get("image_prompt", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "negative_prompt": payload.get("formatted_output", {}).get("negative_prompt", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "style": payload.get("formatted_output", {}).get("style", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "visual_style": payload.get("formatted_output", {}).get("style", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "lighting": payload.get("formatted_output", {}).get("lighting", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "lighting_style": payload.get("formatted_output", {}).get("lighting", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "composition_style": payload.get("formatted_output", {}).get("composition", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "camera": payload.get("formatted_output", {}).get("camera", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "camera_direction": payload.get("formatted_output", {}).get("camera", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "aspect_ratio": payload.get("formatted_output", {}).get("aspect_ratio", "") if isinstance(payload.get("formatted_output"), dict) else "",
                "platform": payload.get("platform", ""),
                "metadata": payload.get("metadata", {}),
            }

        validation = self.image_prompt_validator.validate(image_result)
        prompt_text = str(image_result.get("image_prompt") or image_result.get("prompt") or image_result.get("enhanced_image_prompt") or "").strip()
        image_payload = {
            "brand": payload.get("brand", ""),
            "platform": payload.get("platform", ""),
            "content_type": "image_prompt",
            "formatted_output": {
                "image_prompt": prompt_text,
                "caption": prompt_text,
                "main_message": prompt_text,
                "notes": prompt_text,
                "style": str(image_result.get("style", image_result.get("visual_style", ""))),
                "camera": str(image_result.get("camera", image_result.get("camera_direction", ""))),
                "lighting": str(image_result.get("lighting", image_result.get("lighting_style", ""))),
                "negative_prompt": str(image_result.get("negative_prompt", "")),
            },
            "platform_variants": payload.get("platform_variants", {}),
            "metadata": payload.get("metadata", {}),
        }
        brand_result = self.brand_checker.check(image_payload)
        factual_result = self.factual_safety_checker.check(image_payload)

        quality_result = {
            "score": validation["scores"]["completeness"],
            "warnings": list(validation["warnings"]),
            "errors": list(validation["errors"]),
            "checks": {"image_prompt_validation": validation["scores"]},
        }
        platform_result = {
            "score": validation["scores"]["platform_fit"],
            "warnings": [warning for warning in validation["warnings"] if "platform" in warning.lower() or "aspect ratio" in warning.lower()],
            "errors": [error for error in validation["errors"] if "aspect ratio" in error.lower() or "platform" in error.lower()],
            "checks": {"image_prompt_platform_fit": validation["scores"]["platform_fit"]},
        }
        scores = {
            "quality_score": quality_result["score"],
            "brand_score": brand_result["score"],
            "platform_score": platform_result["score"],
            "factual_safety_score": factual_result["score"],
        }
        warnings = list(dict.fromkeys(quality_result["warnings"] + brand_result["warnings"] + platform_result["warnings"] + factual_result["warnings"]))
        errors = list(dict.fromkeys(quality_result["errors"] + brand_result["errors"] + platform_result["errors"] + factual_result["errors"]))
        checks = {
            "quality": quality_result["checks"],
            "brand": brand_result["checks"],
            "platform": platform_result["checks"],
            "factual_safety": factual_result["checks"],
            "image_prompt_validation": validation,
        }
        recommendations = []
        if validation["scores"]["realism"] < 75:
            recommendations.append("Strengthen realism cues and reduce exaggerated visual language.")
        if validation["scores"]["completeness"] < 85:
            recommendations.append("Add missing visual prompt fields before export.")
        if validation["scores"]["brand_fit"] < 80:
            recommendations.append("Align the prompt more closely with premium but approachable brand language.")
        if validation["scores"]["platform_fit"] < 80:
            recommendations.append("Adjust aspect ratio or platform framing for better fit.")
        if factual_result["score"] < 90:
            recommendations.append("Remove any unsupported property claims from the visual prompt.")
        return self.build_final_decision(scores=scores, warnings=warnings, errors=errors, checks=checks, recommendations=recommendations, payload=payload)

    def _evaluate_creative_direction(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate creative direction guidance."""

        creative_result = payload.get("creative_direction_result")
        if not isinstance(creative_result, dict) or not creative_result:
            creative_result = {
                "creative_direction_type": str(payload.get("creative_direction_type", "") or ""),
                "brand": payload.get("brand", ""),
                "campaign_type": payload.get("campaign_type", ""),
                "visual_identity": payload.get("visual_identity", {}),
                "moodboard": payload.get("moodboard", {}),
                "color_palette": payload.get("color_palette", {}),
                "lighting_direction": payload.get("lighting_direction", ""),
                "camera_style": payload.get("camera_style", ""),
                "composition_rules": payload.get("composition_rules", []),
                "platform_guidelines": payload.get("platform_creative_guidelines", payload.get("platform_guidelines", {})),
                "media_guidelines": payload.get("media_guidelines", {}),
                "asset_guidelines": payload.get("asset_guidelines", {}),
                "creative_direction": payload.get("creative_direction", ""),
                "metadata": payload.get("metadata", {}),
            }

        validation = self.creative_direction_validator.validate(creative_result)
        brand_result = self.brand_checker.check({
            "brand": payload.get("brand", ""),
            "platform": payload.get("platform", ""),
            "content_type": "creative_direction",
            "formatted_output": {
                "title": str(creative_result.get("creative_direction_type", "")),
                "short_description": str(creative_result.get("lighting_direction", "")),
                "long_description": str(creative_result.get("camera_style", "")),
                "highlights": [rule.get("description", "") for rule in creative_result.get("composition_rules", []) if isinstance(rule, dict)],
                "cta": "",
            },
            "platform_variants": payload.get("platform_variants", {}),
            "metadata": payload.get("metadata", {}),
        })
        platform_result = {
            "score": validation["scores"]["platform_fit"],
            "warnings": [],
            "errors": [],
            "checks": {"creative_direction_platform_fit": validation["scores"]["platform_fit"]},
        }
        factual_result = {
            "score": validation["scores"]["realism"],
            "warnings": list(validation["warnings"]),
            "errors": list(validation["errors"]),
            "checks": {"creative_direction_realism": validation["scores"]["realism"]},
        }
        quality_result = {
            "score": validation["scores"]["completeness"],
            "warnings": list(validation["warnings"]),
            "errors": list(validation["errors"]),
            "checks": {"creative_direction_completeness": validation["scores"]["completeness"]},
        }
        scores = {
            "quality_score": quality_result["score"],
            "brand_score": brand_result["score"],
            "platform_score": platform_result["score"],
            "factual_safety_score": factual_result["score"],
        }
        warnings = list(dict.fromkeys(validation["warnings"] + brand_result["warnings"]))
        errors = list(dict.fromkeys(validation["errors"] + brand_result["errors"]))
        checks = {
            "quality": quality_result["checks"],
            "brand": brand_result["checks"],
            "platform": platform_result["checks"],
            "factual_safety": factual_result["checks"],
            "creative_direction_validation": validation,
        }
        recommendations = []
        if validation["scores"]["brand_fit"] < 80:
            recommendations.append("Align the creative direction more closely with the selected visual identity.")
        if validation["scores"]["visual_consistency"] < 80:
            recommendations.append("Strengthen palette, lighting, and composition consistency.")
        if validation["scores"]["platform_fit"] < 80:
            recommendations.append("Refine the platform-specific creative guidance.")
        if validation["scores"]["realism"] < 80:
            recommendations.append("Remove exaggerated or unrealistic visual cues.")
        if validation["scores"]["completeness"] < 80:
            recommendations.append("Add clearer moodboard and media guidance.")
        return self.build_final_decision(scores=scores, warnings=warnings, errors=errors, checks=checks, recommendations=recommendations, payload=payload)

    def _evaluate_video_script(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate video script results with prompt-specific safety checks."""

        video_result = payload.get("video_script_result")
        if not isinstance(video_result, dict) or not video_result:
            formatted_output = payload.get("formatted_output", {})
            if isinstance(formatted_output, dict):
                video_result = {
                    "hook": formatted_output.get("hook", ""),
                    "script": formatted_output.get("script", ""),
                    "voiceover": formatted_output.get("voiceover", formatted_output.get("voiceover_direction", "")),
                    "cta": formatted_output.get("cta", ""),
                    "music_mood": formatted_output.get("music_mood", formatted_output.get("mood", "")),
                    "scene_sequence": formatted_output.get("scene_sequence", formatted_output.get("sequence", [])),
                    "storyboard": formatted_output.get("storyboard", []),
                    "camera_direction": formatted_output.get("camera_direction", formatted_output.get("camera_motion", "")),
                    "duration": formatted_output.get("duration", payload.get("metadata", {}).get("duration", "")) if isinstance(payload.get("metadata"), dict) else formatted_output.get("duration", ""),
                    "platform": payload.get("platform", ""),
                    "metadata": payload.get("metadata", {}),
                }
            else:
                video_result = {}

        validation = self.video_script_validator.validate(video_result)
        script_text = str(video_result.get("script") or video_result.get("voiceover") or "").strip()
        video_payload = {
            "brand": payload.get("brand", ""),
            "platform": payload.get("platform", ""),
            "content_type": "video_script",
            "formatted_output": {
                "hook": str(video_result.get("hook", "")),
                "script": script_text,
                "voiceover": str(video_result.get("voiceover", video_result.get("voiceover_direction", ""))),
                "cta": str(video_result.get("cta", "")),
                "music_mood": str(video_result.get("music_mood", video_result.get("mood", ""))),
                "scene_sequence": video_result.get("scene_sequence", video_result.get("sequence", [])),
                "storyboard": video_result.get("storyboard", []),
                "camera_direction": video_result.get("camera_direction", video_result.get("camera_motion", "")),
            },
            "platform_variants": payload.get("platform_variants", {}),
            "metadata": payload.get("metadata", {}),
        }
        brand_result = self.brand_checker.check(video_payload)
        factual_result = self.factual_safety_checker.check(video_payload)

        quality_result = {
            "score": validation["scores"]["structure"],
            "warnings": list(validation["warnings"]),
            "errors": list(validation["errors"]),
            "checks": {"video_script_validation": validation["scores"]},
        }
        platform_result = {
            "score": validation["scores"]["platform_fit"],
            "warnings": [warning for warning in validation["warnings"] if "platform" in warning.lower() or "duration" in warning.lower() or "scene" in warning.lower()],
            "errors": [error for error in validation["errors"] if "duration" in error.lower() or "scene" in error.lower() or "storyboard" in error.lower()],
            "checks": {"video_script_platform_fit": validation["scores"]["platform_fit"]},
        }
        scores = {
            "quality_score": quality_result["score"],
            "brand_score": brand_result["score"],
            "platform_score": platform_result["score"],
            "factual_safety_score": factual_result["score"],
        }
        warnings = list(dict.fromkeys(quality_result["warnings"] + brand_result["warnings"] + platform_result["warnings"] + factual_result["warnings"]))
        errors = list(dict.fromkeys(quality_result["errors"] + brand_result["errors"] + platform_result["errors"] + factual_result["errors"]))
        checks = {
            "quality": quality_result["checks"],
            "brand": brand_result["checks"],
            "platform": platform_result["checks"],
            "factual_safety": factual_result["checks"],
            "video_script_validation": validation,
        }
        recommendations = []
        if validation["scores"]["structure"] < 75:
            recommendations.append("Strengthen the hook, scene sequence, and CTA structure.")
        if validation["scores"]["pacing"] < 75:
            recommendations.append("Tighten pacing and align the scene count with the duration.")
        if validation["scores"]["platform_fit"] < 80:
            recommendations.append("Adjust framing, pacing, or CTA timing for the platform.")
        if validation["scores"]["factual_safety"] < 90:
            recommendations.append("Remove unsupported property claims from the script.")
        return self.build_final_decision(scores=scores, warnings=warnings, errors=errors, checks=checks, recommendations=recommendations, payload=payload)

    def _evaluate_token_usage(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Evaluate token usage metadata and emit warnings only."""

        token_usage = payload.get("token_usage")
        if not isinstance(token_usage, dict) or not token_usage:
            return {"warnings": ["Token usage missing from payload."], "errors": [], "checks": {"present": False}}

        validation = self.token_validator.validate(token_usage)
        warnings = list(validation.get("warnings", []))
        errors = list(validation.get("errors", []))
        checks = dict(validation.get("checks", {}))
        warnings.extend([str(item).strip() for item in token_usage.get("warnings", []) if str(item).strip()] if isinstance(token_usage.get("warnings"), list) else [])
        errors.extend([str(item).strip() for item in token_usage.get("errors", []) if str(item).strip()] if isinstance(token_usage.get("errors"), list) else [])
        if int(token_usage.get("total_tokens", 0) or 0) >= 12000:
            warnings.append("Suspiciously high token usage detected.")
        if not checks.get("provider_present"):
            warnings.append("Token usage provider metadata is missing.")
        return {
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
            "checks": checks,
        }

    def _merge_token_analysis(self, result: dict[str, Any], token_result: dict[str, Any]) -> dict[str, Any]:
        """Merge token tracking warnings and checks into an existing governance result."""

        if not isinstance(result, dict):
            return result
        merged = dict(result)
        merged["warnings"] = list(dict.fromkeys(list(merged.get("warnings", [])) + list(token_result.get("warnings", []))))
        merged["errors"] = list(dict.fromkeys(list(merged.get("errors", [])) + list(token_result.get("errors", []))))
        checks = dict(merged.get("checks", {}))
        checks["token_tracking"] = token_result.get("checks", {})
        merged["checks"] = checks
        return merged

    def _build_recommendations(self, quality_result: dict[str, Any], brand_result: dict[str, Any], platform_result: dict[str, Any], factual_result: dict[str, Any]) -> list[str]:
        recommendations: list[str] = []
        if quality_result["score"] < 75:
            recommendations.append("Strengthen the hook, CTA, and value proposition.")
        if brand_result["score"] < 80:
            recommendations.append("Reinforce trustworthy, premium-but-approachable brand language.")
        if platform_result["score"] < 80:
            recommendations.append("Adjust the output more closely to the target platform format.")
        if factual_result["score"] < 90:
            recommendations.append("Remove or verify any risky real estate claims before publishing.")
        return recommendations

    def _is_critical_safety_error(self, error: str) -> bool:
        lowered = error.lower()
        return any(term in lowered for term in ("critical safety", "guaranteed roi", "guaranteed return", "risk-free investment", "fake exclusivity", "fake scarcity", "fake urgency"))

    def _is_non_empty(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list):
            return bool(value)
        if isinstance(value, dict):
            return bool(value)
        return True

    def _serialize_content(self, content: dict[str, Any]) -> str:
        pieces: list[str] = []
        for value in content.values():
            if isinstance(value, str):
                pieces.append(value)
            elif isinstance(value, list):
                pieces.extend([str(item) for item in value])
        return "\n".join(pieces)

    def build_analytics_snapshot(self, governance_result: dict[str, Any]) -> dict[str, Any]:
        """Build a safe governance analytics snapshot."""

        return {
            "status": str(governance_result.get("status", "unknown")),
            "approved": bool(governance_result.get("approved", False)),
            "quality_score": float(governance_result.get("quality_score", 0.0) or 0.0),
            "brand_score": float(governance_result.get("brand_score", 0.0) or 0.0),
            "platform_score": float(governance_result.get("platform_score", 0.0) or 0.0),
            "factual_safety_score": float(governance_result.get("factual_safety_score", 0.0) or 0.0),
            "overall_score": float(governance_result.get("overall_score", 0.0) or 0.0),
            "warning_count": len(governance_result.get("warnings", []) or []),
            "error_count": len(governance_result.get("errors", []) or []),
            "recommendation_count": len(governance_result.get("recommendations", []) or []),
        }


if __name__ == "__main__":
    engine = ContentGovernanceEngine()
    sample_post = {
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "property_description",
        "formatted_output": {
            "title": "Rustic home near Sant Llorenc des Cardassar",
            "short_description": "A calm Mallorca property with modern comfort.",
            "long_description": "Rustic outside, modern inside, with practical access to services and nearby beaches.",
            "highlights": ["Quiet setting", "Modern interiors", "Near beaches"],
            "cta": "Request a viewing",
            "hashtags": ["#Mallorca"],
        },
        "metadata": {
            "audience": "relocation_clients",
            "location": "sant_llorenc_des_cardassar",
            "objective": "generate_leads",
        },
    }
    sample_risky = {
        "brand": "wenzel_partner",
        "platform": "website_listing",
        "content_type": "property_description",
        "formatted_output": {
            "title": "Exclusive opportunity",
            "short_description": "Best investment on the island.",
            "long_description": "Guaranteed ROI and risk-free investment in a limited time only offer.",
            "highlights": ["Guaranteed appreciation", "Unbeatable price"],
            "cta": "Act now",
        },
        "metadata": {"audience": "investors", "location": "mallorca", "objective": "generate_leads"},
    }
    print(engine.evaluate(sample_post))
    print(engine.evaluate({
        **sample_post,
        "platform_variants": {
            "linkedin": {
                "content": {
                    "headline": "Mallorca property with practical lifestyle appeal",
                    "body": "Professional market insight with calm, local positioning.",
                    "cta": "Request details",
                    "hashtags": ["#Mallorca"],
                }
            }
        },
    }))
    print(engine.evaluate(sample_risky))
