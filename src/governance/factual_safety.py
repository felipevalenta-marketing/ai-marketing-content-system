"""Factual safety checks for real estate marketing content."""

from __future__ import annotations

from typing import Any

from src.governance.governance_rules import get_governance_rules
from src.adapters.platform_contracts import normalize_platform_name
from src.output.output_contracts import normalize_output_content_type


class FactualSafetyChecker:
    """Detect risky or unsupported real estate claims."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or get_governance_rules()

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return factual safety diagnostics."""

        text = self._collect_text(payload)
        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}
        lowered = text.lower()

        critical = self.rules["real_estate_safety_rules"]["critical_phrases"]
        warning_phrases = self.rules["real_estate_safety_rules"]["warning_phrases"]
        unsupported = self.rules["real_estate_safety_rules"]["unsupported_claim_phrases"]
        risky_hits = [phrase for phrase in critical if phrase in lowered]
        warning_hits = [phrase for phrase in warning_phrases if phrase in lowered]
        unsupported_hits = [phrase for phrase in unsupported if phrase in lowered]
        invented_distance = self._detect_invented_distance(text)
        invented_feature = self._detect_invented_feature(text)

        if risky_hits:
            errors.append(f"Critical safety phrases detected: {', '.join(risky_hits)}")
        if warning_hits:
            warnings.append(f"Risky claim phrases detected: {', '.join(warning_hits)}")
        if unsupported_hits:
            warnings.append(f"Unsupported claim phrases detected: {', '.join(unsupported_hits)}")
        if invented_distance:
            errors.append("Potential invented distance or location claim detected.")
        if invented_feature:
            errors.append("Potential invented property feature claim detected.")

        score = 100.0
        score -= 35 if risky_hits else 0
        score -= min(18, 6 * len(warning_hits))
        score -= min(18, 6 * len(unsupported_hits))
        score -= 15 if invented_distance else 0
        score -= 15 if invented_feature else 0

        checks.update(
            {
                "critical_hits": risky_hits,
                "warning_hits": warning_hits,
                "unsupported_hits": unsupported_hits,
                "invented_distance": invented_distance,
                "invented_feature": invented_feature,
                "platform": normalize_platform_name(str(payload.get("platform", ""))),
                "content_type": normalize_output_content_type(str(payload.get("content_type", ""))),
            }
        )
        return {"score": max(0.0, round(score, 2)), "warnings": warnings, "errors": errors, "checks": checks}

    def _collect_text(self, payload: dict[str, Any]) -> str:
        output = {}
        if isinstance(payload.get("formatted_output"), dict):
            output = dict(payload["formatted_output"])
        elif isinstance(payload.get("platform_variants"), dict):
            platform = payload.get("platform") or next(iter(payload["platform_variants"]), None)
            variant = payload["platform_variants"].get(platform) if platform else None
            if isinstance(variant, dict):
                content = variant.get("content")
                if isinstance(content, dict):
                    output = dict(content)
        else:
            output = dict(payload or {})
        pieces: list[str] = []
        for key in ("hook", "caption", "post", "body", "title", "short_description", "long_description", "cta", "subject", "preview_text", "scene_description", "script", "main_message", "notes"):
            value = output.get(key)
            if isinstance(value, str) and value.strip():
                pieces.append(value.strip())
        for key in ("highlights", "hashtags", "sequence", "assets"):
            value = output.get(key)
            if isinstance(value, list):
                pieces.extend([str(item).strip() for item in value if str(item).strip()])
        return "\n".join(pieces)

    def _detect_invented_distance(self, text: str) -> bool:
        lowered = text.lower()
        patterns = ("minutes from", "hours from", "km from", "kilometers from", "meters from", "5 min from", "10 min from")
        return any(pattern in lowered for pattern in patterns)

    def _detect_invented_feature(self, text: str) -> bool:
        lowered = text.lower()
        patterns = ("private beach", "direct beach access", "guaranteed rental", "lock and leave", "fully licensed investment")
        return any(pattern in lowered for pattern in patterns)
