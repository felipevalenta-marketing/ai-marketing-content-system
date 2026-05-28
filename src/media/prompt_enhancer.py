"""Prompt cleanup and optimization helpers for image prompt generation."""

from __future__ import annotations

from typing import Any
import re


class PromptEnhancer:
    """Improve and normalize image prompts without inventing new facts."""

    def enhance(self, base_prompt: str, style: dict[str, Any], rules: dict[str, Any], request: dict[str, Any]) -> str:
        """Enhance a base prompt with cinematic and safety language."""

        prompt = self.clean_prompt(base_prompt)
        style_name = str(style.get("name", "")).strip()
        if style_name:
            prompt = f"{prompt} Style: {style.get('mood', '')}. " if prompt else f"Style: {style.get('mood', '')}. "
        if rules:
            fragments = [str(rule.get("prompt_fragment", "")).strip() for rule in rules if isinstance(rule, dict)]
            fragments = [fragment for fragment in fragments if fragment]
            if fragments:
                prompt = f"{prompt} {' '.join(fragments)}"
        prompt = self.enforce_realism(prompt)
        prompt = self.enforce_brand_safety(prompt)
        prompt = self.optimize_prompt_length(prompt)
        return self.remove_duplicate_phrases(prompt)

    def clean_prompt(self, prompt: str) -> str:
        """Normalize whitespace and trim filler."""

        text = str(prompt or "").strip()
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\s+([,.;:])", r"\1", text)
        return text.strip()

    def remove_duplicate_phrases(self, prompt: str) -> str:
        """Remove repeated sentences and clauses."""

        text = self.clean_prompt(prompt)
        if not text:
            return ""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        unique_sentences: list[str] = []
        seen: set[str] = set()
        for sentence in sentences:
            normalized = sentence.strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_sentences.append(sentence.strip())
        return " ".join(unique_sentences).strip()

    def enforce_realism(self, prompt: str) -> str:
        """Reduce language that can imply impossible or fake visuals."""

        text = self.clean_prompt(prompt)
        replacements = {
            "fake luxury": "premium realism",
            "impossible": "believable",
            "fantasy": "grounded",
            "cgi look": "photorealistic look",
            "overly glossy": "natural finish",
            "unrealistic lighting": "natural lighting",
            "fake exclusivity": "exclusive-feeling but verifiable",
        }
        for source, target in replacements.items():
            text = re.sub(re.escape(source), target, text, flags=re.IGNORECASE)
        return self.clean_prompt(text)

    def enforce_brand_safety(self, prompt: str) -> str:
        """Remove unsupported hype or risky claim language."""

        text = self.clean_prompt(prompt)
        banned = (
            "guaranteed roi",
            "guaranteed return",
            "risk-free investment",
            "fake scarcity",
            "fake urgency",
            "best investment",
            "unbeatable price",
        )
        for phrase in banned:
            text = re.sub(re.escape(phrase), "premium and realistic", text, flags=re.IGNORECASE)
        return self.clean_prompt(text)

    def optimize_prompt_length(self, prompt: str) -> str:
        """Keep prompts compact enough for prompt usability."""

        text = self.clean_prompt(prompt)
        if len(text) <= 900:
            return text
        sentences = re.split(r"(?<=[.!?])\s+", text)
        trimmed: list[str] = []
        total = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if total + len(sentence) > 900:
                break
            trimmed.append(sentence)
            total += len(sentence) + 1
        return " ".join(trimmed).strip()
