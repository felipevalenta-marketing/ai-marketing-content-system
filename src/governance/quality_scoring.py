"""Quality scoring heuristics for generated content."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re

from src.governance.governance_rules import get_governance_rules
from src.utils.file_utils import normalize_key


@dataclass(frozen=True)
class QualityScoreResult:
    """Quality score result."""

    score: float
    warnings: list[str]
    errors: list[str]
    checks: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "warnings": self.warnings,
            "errors": self.errors,
            "checks": self.checks,
        }


class QualityScorer:
    """Assess content quality deterministically."""

    def __init__(self, rules: dict[str, Any] | None = None) -> None:
        self.rules = rules or get_governance_rules()

    def score(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return a deterministic quality score."""

        output = self._extract_primary_output(payload)
        text = self._collect_text(output)
        warnings: list[str] = []
        errors: list[str] = []
        deductions = 0.0
        checks: dict[str, Any] = {}

        if not text.strip():
            errors.append("Content is empty.")
            return QualityScoreResult(score=0.0, warnings=warnings, errors=errors, checks={"empty": True}).to_dict()

        hook = self._get_field(output, "hook", "title", "headline", "subject")
        cta = self._get_field(output, "cta")
        repetitive = self._has_repetition(text)
        generic_phrases = self._find_matches(text, self.rules["generic_ai_phrases"])
        hype_terms = self._find_matches(text, self.rules["excessive_hype_terms"])
        adjective_count = self._count_adjectives(text)
        readability = self._readability_score(text)
        value_prop = self._has_value_proposition(text)
        audience_fit = self._has_audience_fit(payload)
        structure_score = self._structure_score(output)

        if self._is_empty(hook):
            warnings.append("Weak or missing hook.")
            deductions += 12
        if self._is_empty(cta):
            warnings.append("Missing CTA.")
            deductions += 10
        if repetitive:
            warnings.append("Repetitive wording detected.")
            deductions += 8
        if generic_phrases:
            warnings.append("Generic AI phrasing detected.")
            deductions += min(12, 3 * len(generic_phrases))
        if hype_terms:
            warnings.append("Excessive hype language detected.")
            deductions += min(10, 2 * len(hype_terms))
        if adjective_count > 8:
            warnings.append("Too many adjectives may reduce clarity.")
            deductions += 6
        if readability < 0.45:
            warnings.append("Readability is below the preferred threshold.")
            deductions += 8
        if not value_prop:
            warnings.append("Value proposition is unclear.")
            deductions += 10
        if not audience_fit:
            warnings.append("Audience fit is unclear.")
            deductions += 8
        if structure_score < 0.6:
            warnings.append("Structure completeness could be improved.")
            deductions += 8

        score = max(0.0, min(100.0, 100.0 - deductions))
        checks.update(
            {
                "hook_present": not self._is_empty(hook),
                "cta_present": not self._is_empty(cta),
                "repetitive": repetitive,
                "generic_phrases": generic_phrases,
                "hype_terms": hype_terms,
                "adjective_count": adjective_count,
                "readability": round(readability, 3),
                "value_proposition": value_prop,
                "audience_fit": audience_fit,
                "structure_score": round(structure_score, 3),
            }
        )
        return QualityScoreResult(score=round(score, 2), warnings=warnings, errors=errors, checks=checks).to_dict()

    def _extract_primary_output(self, payload: dict[str, Any]) -> dict[str, Any]:
        if isinstance(payload.get("formatted_output"), dict):
            return dict(payload["formatted_output"])
        if isinstance(payload.get("platform_variants"), dict):
            platform = payload.get("platform") or next(iter(payload["platform_variants"]), None)
            variant = payload["platform_variants"].get(platform) if platform else None
            if isinstance(variant, dict):
                content = variant.get("content")
                if isinstance(content, dict):
                    return dict(content)
        if isinstance(payload, dict):
            return dict(payload)
        return {}

    def _collect_text(self, output: dict[str, Any]) -> str:
        parts: list[str] = []
        for key in ("hook", "caption", "post", "body", "title", "short_description", "long_description", "scene_description", "script", "main_message", "preview_text"):
            value = output.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
        for key in ("highlights", "hashtags", "sequence"):
            value = output.get(key)
            if isinstance(value, list):
                parts.extend([str(item).strip() for item in value if str(item).strip()])
        return "\n".join(parts).strip()

    def _get_field(self, output: dict[str, Any], *names: str) -> str:
        for name in names:
            value = output.get(name)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _has_repetition(self, text: str) -> bool:
        words = [normalize_key(word) for word in re.findall(r"\b\w+\b", text.lower()) if normalize_key(word)]
        if len(words) < 8:
            return False
        unique_ratio = len(set(words)) / len(words)
        return unique_ratio < 0.45

    def _find_matches(self, text: str, phrases: list[str]) -> list[str]:
        lowered = text.lower()
        return [phrase for phrase in phrases if phrase.lower() in lowered]

    def _count_adjectives(self, text: str) -> int:
        words = re.findall(r"\b\w+\b", text.lower())
        adjective_suffixes = ("ous", "ive", "ful", "less", "able", "ible", "al", "ic", "ish", "y")
        return sum(1 for word in words if word.endswith(adjective_suffixes))

    def _readability_score(self, text: str) -> float:
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        words = re.findall(r"\b\w+\b", text)
        if not sentences or not words:
            return 0.0
        avg_sentence_length = len(words) / max(1, len(sentences))
        if avg_sentence_length <= 18:
            return 1.0
        if avg_sentence_length <= 24:
            return 0.8
        if avg_sentence_length <= 32:
            return 0.6
        return 0.35

    def _has_value_proposition(self, text: str) -> bool:
        return bool(re.search(r"\b(benefit|value|lifestyle|location|connect|calm|space|quality|support|guide)\b", text.lower()))

    def _has_audience_fit(self, payload: dict[str, Any]) -> bool:
        audience = str(payload.get("metadata", {}).get("audience") or payload.get("audience") or "").strip().lower()
        return bool(audience)

    def _structure_score(self, output: dict[str, Any]) -> float:
        non_empty = 0
        checked = 0
        for key in ("hook", "caption", "post", "body", "title", "short_description", "long_description", "cta", "subject", "preview_text", "scene_description", "script", "main_message"):
            if key in output:
                checked += 1
                if not self._is_empty(output.get(key)):
                    non_empty += 1
        for key in ("highlights", "hashtags", "sequence", "assets"):
            if key in output:
                checked += 1
                if isinstance(output.get(key), list) and output.get(key):
                    non_empty += 1
        if checked == 0:
            return 0.0
        return non_empty / checked

    def _is_empty(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        if isinstance(value, list):
            return len(value) == 0
        return False
