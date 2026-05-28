"""Governance orchestrator for content approval and review."""

from __future__ import annotations

from typing import Any

from src.governance.brand_compliance import BrandComplianceChecker
from src.governance.factual_safety import FactualSafetyChecker
from src.governance.governance_result import build_governance_failure, build_governance_success
from src.governance.governance_rules import get_governance_rules
from src.governance.platform_compliance import PlatformComplianceChecker
from src.governance.quality_scoring import QualityScorer
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
        warnings = list(dict.fromkeys(
            quality_result["warnings"]
            + brand_result["warnings"]
            + platform_result["warnings"]
            + factual_result["warnings"]
            + formatted_result.get("warnings", [])
        ))
        errors = list(dict.fromkeys(
            quality_result["errors"]
            + brand_result["errors"]
            + platform_result["errors"]
            + factual_result["errors"]
        ))
        checks = {
            "quality": quality_result["checks"],
            "brand": brand_result["checks"],
            "platform": platform_result["checks"],
            "factual_safety": factual_result["checks"],
            "formatted_output": formatted_result.get("checks", {}),
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
