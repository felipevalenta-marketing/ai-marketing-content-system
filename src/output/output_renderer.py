"""Render structured outputs into human-readable and automation-ready formats."""

from __future__ import annotations

from typing import Any
import json
from datetime import datetime

from src.output.output_contracts import get_output_contract, normalize_output_content_type
from src.utils.logger import get_logger, log_warning


class OutputRenderer:
    """Render outputs as markdown, plain text, or JSON-compatible dictionaries."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)

    def render_markdown(self, output: dict[str, Any], content_type: str) -> str:
        """Render a clean markdown representation."""

        canonical_type = normalize_output_content_type(content_type)
        contract = get_output_contract(canonical_type)
        try:
            lines: list[str] = [f"# {canonical_type.replace('_', ' ').title()}"]
            lines.extend(self._render_sections(output, contract.content_type))
            metadata = output.get("metadata") or output.get("output_metadata") or {}
            if metadata:
                lines.append("")
                lines.append("## Metadata")
                for key, value in metadata.items():
                    lines.append(f"- **{key}**: {self._stringify(value)}")
            validation = output.get("validation_result") or {}
            warnings = validation.get("warnings") or output.get("formatting_warnings") or output.get("parser_warnings") or []
            if warnings:
                lines.append("")
                lines.append("## Validation Warnings")
                for warning in warnings:
                    lines.append(f"- {warning}")
            return "\n".join(lines).strip()
        except Exception as exc:  # pragma: no cover - defensive fallback
            log_warning(self.logger, f"Markdown rendering failed: {exc}")
            return self.render_text(output, content_type)

    def render_text(self, output: dict[str, Any], content_type: str) -> str:
        """Render a plain text version suitable for copying into tools."""

        canonical_type = normalize_output_content_type(content_type)
        contract = get_output_contract(canonical_type)
        sections = self._render_sections(output, contract.content_type)
        cleaned = []
        for line in sections:
            cleaned.append(line.replace("## ", "").replace("### ", "").strip())
        return "\n".join(part for part in cleaned if part).strip()

    def render_json(self, output: dict[str, Any]) -> dict[str, Any]:
        """Return a JSON-friendly copy of the output."""

        return json.loads(json.dumps(output, ensure_ascii=False, default=str))

    def _render_sections(self, output: dict[str, Any], content_type: str) -> list[str]:
        """Render content-type specific markdown sections."""

        if content_type == "instagram_post":
            return self._render_instagram_post(output)
        if content_type == "instagram_reel":
            return self._render_instagram_reel(output)
        if content_type == "property_description":
            return self._render_property_description(output)
        if content_type == "image_prompt":
            return self._render_image_prompt(output)
        if content_type == "video_prompt":
            return self._render_video_prompt(output)
        if content_type == "video_script":
            return self._render_video_script(output)
        return self._render_campaign_asset(output)

    def _render_instagram_post(self, output: dict[str, Any]) -> list[str]:
        lines = ["", "## Hook", self._stringify(output.get("hook", "")), "", "## Caption", self._stringify(output.get("caption", ""))]
        hashtags = output.get("hashtags") or []
        if hashtags:
            lines.extend(["", "## Hashtags", " ".join(hashtags)])
        cta = output.get("cta")
        if cta:
            lines.extend(["", "## CTA", self._stringify(cta)])
        notes = output.get("notes")
        if notes:
            lines.extend(["", "## Notes", self._stringify(notes)])
        return lines

    def _render_instagram_reel(self, output: dict[str, Any]) -> list[str]:
        lines = [
            "",
            "## Hook",
            self._stringify(output.get("hook", "")),
            "",
            "## Script",
            self._stringify(output.get("script", "")),
            "",
            "## Scene Direction",
            self._stringify(output.get("scene_direction", "")),
        ]
        sequence = output.get("sequence") or []
        if sequence:
            lines.extend(["", "## Sequence"])
            lines.extend([f"- {self._stringify(item)}" for item in sequence])
        hashtags = output.get("hashtags") or []
        if hashtags:
            lines.extend(["", "## Hashtags", " ".join(hashtags)])
        cta = output.get("cta")
        if cta:
            lines.extend(["", "## CTA", self._stringify(cta)])
        notes = output.get("notes")
        if notes:
            lines.extend(["", "## Notes", self._stringify(notes)])
        return lines

    def _render_property_description(self, output: dict[str, Any]) -> list[str]:
        lines = [
            "",
            "## Title",
            self._stringify(output.get("title", "")),
            "",
            "## Short Description",
            self._stringify(output.get("short_description", "")),
            "",
            "## Long Description",
            self._stringify(output.get("long_description", "")),
        ]
        highlights = output.get("highlights") or []
        if highlights:
            lines.extend(["", "## Highlights"])
            lines.extend([f"- {self._stringify(item)}" for item in highlights])
        cta = output.get("cta")
        if cta:
            lines.extend(["", "## CTA", self._stringify(cta)])
        notes = output.get("notes")
        if notes:
            lines.extend(["", "## Notes", self._stringify(notes)])
        return lines

    def _render_image_prompt(self, output: dict[str, Any]) -> list[str]:
        lines = [
            "",
            "## Visual Direction",
            self._stringify(output.get("visual_direction", "")),
            "",
            "## Subject",
            self._stringify(output.get("subject", "")),
            "",
            "## Composition",
            self._stringify(output.get("composition", "")),
            "",
            "## Lighting",
            self._stringify(output.get("lighting", "")),
            "",
            "## Style",
            self._stringify(output.get("style", "")),
        ]
        negative_prompt = output.get("negative_prompt")
        if negative_prompt:
            lines.extend(["", "## Negative Prompt", self._stringify(negative_prompt)])
        notes = output.get("notes")
        if notes:
            lines.extend(["", "## Notes", self._stringify(notes)])
        return lines

    def _render_video_prompt(self, output: dict[str, Any]) -> list[str]:
        lines = [
            "",
            "## Scene Description",
            self._stringify(output.get("scene_description", "")),
            "",
            "## Camera Motion",
            self._stringify(output.get("camera_motion", "")),
            "",
            "## Mood",
            self._stringify(output.get("mood", "")),
        ]
        sequence = output.get("sequence") or []
        if sequence:
            lines.extend(["", "## Sequence"])
            lines.extend([f"- {self._stringify(item)}" for item in sequence])
        voiceover = output.get("voiceover_direction")
        if voiceover:
            lines.extend(["", "## Voiceover Direction", self._stringify(voiceover)])
        notes = output.get("notes")
        if notes:
            lines.extend(["", "## Notes", self._stringify(notes)])
        return lines

    def _render_video_script(self, output: dict[str, Any]) -> list[str]:
        lines = [
            "",
            "## Hook",
            self._stringify(output.get("hook", "")),
            "",
            "## Script",
            self._stringify(output.get("script", "")),
            "",
            "## Voiceover",
            self._stringify(output.get("voiceover", "")),
            "",
            "## Music Mood",
            self._stringify(output.get("music_mood", "")),
        ]
        scene_sequence = output.get("scene_sequence") or []
        if scene_sequence:
            lines.extend(["", "## Scene Sequence"])
            for item in scene_sequence:
                lines.append(f"- {self._stringify(item)}")
        storyboard = output.get("storyboard") or []
        if storyboard:
            lines.extend(["", "## Storyboard"])
            for item in storyboard:
                lines.append(f"- {self._stringify(item)}")
        camera_direction = output.get("camera_direction")
        if camera_direction:
            lines.extend(["", "## Camera Direction", self._stringify(camera_direction)])
        cta = output.get("cta")
        if cta:
            lines.extend(["", "## CTA", self._stringify(cta)])
        notes = output.get("notes")
        if notes:
            lines.extend(["", "## Notes", self._stringify(notes)])
        return lines

    def _render_campaign_asset(self, output: dict[str, Any]) -> list[str]:
        lines = [
            "",
            "## Campaign Name",
            self._stringify(output.get("campaign_name", "")),
            "",
            "## Objective",
            self._stringify(output.get("objective", "")),
            "",
            "## Main Message",
            self._stringify(output.get("main_message", "")),
        ]
        assets = output.get("assets") or []
        if assets:
            lines.extend(["", "## Assets"])
            lines.extend([f"- {self._stringify(item)}" for item in assets])
        cta = output.get("cta")
        if cta:
            lines.extend(["", "## CTA", self._stringify(cta)])
        notes = output.get("notes")
        if notes:
            lines.extend(["", "## Notes", self._stringify(notes)])
        return lines

    def _stringify(self, value: Any) -> str:
        """Convert values into readable text."""

        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, list):
            return ", ".join(self._stringify(item) for item in value if self._stringify(item))
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False, default=str)
        return str(value).strip()
