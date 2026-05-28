"""Enhance video scripts for pacing, realism, and brand safety."""

from __future__ import annotations

from typing import Any
import re

from src.utils.file_utils import normalize_markdown_content


class VideoPromptEnhancer:
    """Refine short-form video scripts without inventing new facts."""

    def enhance_script(self, script: str, request: dict[str, Any]) -> str:
        """Clean and refine a draft script."""

        cleaned = self.clean_script(script)
        cleaned = self.remove_duplicate_phrases(cleaned)
        cleaned = self.enforce_brand_safety(cleaned)
        cleaned = self.enforce_pacing(cleaned, str(request.get("duration", "")))
        cleaned = self.optimize_voiceover_length(cleaned, str(request.get("duration", "")))
        return cleaned.strip()

    def clean_script(self, script: str) -> str:
        """Normalize whitespace and remove markdown noise."""

        cleaned = normalize_markdown_content(script or "")
        cleaned = cleaned.replace("```", "")
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def remove_duplicate_phrases(self, script: str) -> str:
        """Collapse repeated lines and phrases."""

        if not script:
            return ""
        lines = [line.strip() for line in script.splitlines() if line.strip()]
        unique_lines: list[str] = []
        seen = set()
        for line in lines:
            key = re.sub(r"\s+", " ", line.lower())
            if key in seen:
                continue
            seen.add(key)
            unique_lines.append(line)
        return "\n".join(unique_lines)

    def enforce_pacing(self, script: str, duration: str) -> str:
        """Keep the script paced for the target duration."""

        if not script:
            return ""
        duration_key = str(duration or "").strip().lower()
        if duration_key in {"15s", "30s"}:
            lines = [line.strip() for line in script.splitlines() if line.strip()]
            return "\n".join(lines[: max(4, min(8, len(lines)))])
        return script

    def enforce_brand_safety(self, script: str) -> str:
        """Remove unsafe urgency or luxury exaggeration."""

        replacements = {
            r"\bguaranteed ROI\b": "strong value potential",
            r"\bguaranteed return\b": "possible long-term appeal",
            r"\brisk[- ]free investment\b": "considered opportunity",
            r"\bfake exclusivity\b": "premium positioning",
            r"\blimited time only\b": "available now",
            r"\bact now\b": "reach out to learn more",
            r"\bbest investment\b": "interesting investment",
            r"\bultimate\b": "premium",
            r"\bworld[- ]class\b": "premium",
        }
        updated = script
        for pattern, replacement in replacements.items():
            updated = re.sub(pattern, replacement, updated, flags=re.IGNORECASE)
        return updated

    def optimize_voiceover_length(self, script: str, duration: str) -> str:
        """Trim the script to a practical voiceover length."""

        if not script:
            return ""
        max_words = self._max_words_for_duration(duration)
        words = script.split()
        if len(words) <= max_words:
            return script
        return " ".join(words[:max_words]).rstrip(" ,;:-") + "."

    def _max_words_for_duration(self, duration: str) -> int:
        key = str(duration or "").strip().lower()
        mapping = {"15s": 34, "30s": 68, "45s": 96, "60s": 120, "90s": 170}
        return mapping.get(key, 68)
