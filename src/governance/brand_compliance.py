"""Brand compliance checks for content governance."""

from __future__ import annotations

from typing import Any

from src.governance.governance_rules import get_governance_rules


class BrandComplianceChecker:
    """Check whether content aligns with brand tone and positioning."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or get_governance_rules()

    def check(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return brand alignment diagnostics."""

        output = self._extract_output(payload)
        text = self._collect_text(output)
        warnings: list[str] = []
        errors: list[str] = []
        checks: dict[str, Any] = {}

        positive = self.rules["brand_tone_signals"]["positive"]
        negative = self.rules["brand_tone_signals"]["negative"]
        lower = text.lower()

        positive_hits = [term for term in positive if term in lower]
        negative_hits = [term for term in negative if term in lower]
        mallorca_relevance = any(term in lower for term in ("mallorca", "palma", "balearic", "sant", "port", "beach", "coast", "coastal", "island"))
        ultra_luxury_only = "ultra-luxury" in lower or "ultra luxury" in lower
        aggressive_pressure = any(term in lower for term in ("act now", "buy now", "don’t miss", "don't miss", "hurry", "limited time"))
        emoji_count = text.count("😊") + text.count("✨") + text.count("🔥") + text.count("🏡") + text.count("🌴")

        if not positive_hits:
            warnings.append("Brand tone could be more trustworthy, local, premium, and approachable.")
        if negative_hits:
            warnings.append(f"Potential brand tone drift detected: {', '.join(negative_hits)}")
        if ultra_luxury_only:
            warnings.append("Content appears positioned as ultra-luxury only.")
        if aggressive_pressure:
            warnings.append("Content uses aggressive pressure language.")
        if emoji_count > 3:
            warnings.append("Emoji usage may be excessive for premium real estate positioning.")

        if ultra_luxury_only:
            errors.append("Unsupported ultra-luxury-only positioning.")
        if aggressive_pressure:
            errors.append("Aggressive sales pressure is not permitted.")

        score = 100.0
        score -= min(20, 4 * len(negative_hits))
        score -= 10 if ultra_luxury_only else 0
        score -= 10 if aggressive_pressure else 0
        score -= 5 if emoji_count > 3 else 0
        score -= 5 if not mallorca_relevance and payload.get("metadata", {}).get("location") else 0
        score -= 5 if not positive_hits else 0

        checks.update(
            {
                "positive_hits": positive_hits,
                "negative_hits": negative_hits,
                "mallorca_relevance": mallorca_relevance,
                "ultra_luxury_only": ultra_luxury_only,
                "aggressive_pressure": aggressive_pressure,
                "emoji_count": emoji_count,
            }
        )
        return {"score": max(0.0, round(score, 2)), "warnings": warnings, "errors": errors, "checks": checks}

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

    def _collect_text(self, output: dict[str, Any]) -> str:
        pieces: list[str] = []
        for key in ("hook", "caption", "post", "body", "title", "short_description", "long_description", "main_message", "cta"):
            value = output.get(key)
            if isinstance(value, str) and value.strip():
                pieces.append(value.strip())
        return "\n".join(pieces)
