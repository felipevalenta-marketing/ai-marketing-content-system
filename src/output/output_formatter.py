"""Normalize parsed AI outputs into export-ready contracts."""

from __future__ import annotations

from typing import Any
import json
import re

from src.output.output_contracts import get_output_contract, normalize_output_content_type
from src.utils.file_utils import normalize_markdown_content
from src.utils.logger import get_logger, log_warning


class OutputFormatter:
    """Convert parsed outputs into predictable structured assets."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)

    def format(self, parsed_output: dict[str, Any], content_type: str) -> dict[str, Any]:
        """Dispatch formatting to the correct content-type handler."""

        canonical_type = normalize_output_content_type(content_type)
        if canonical_type == "instagram_post":
            return self.format_instagram_post(parsed_output)
        if canonical_type == "instagram_reel":
            return self.format_instagram_reel(parsed_output)
        if canonical_type == "property_description":
            return self.format_property_description(parsed_output)
        if canonical_type == "image_prompt":
            return self.format_image_prompt(parsed_output)
        if canonical_type == "video_prompt":
            return self.format_video_prompt(parsed_output)
        if canonical_type == "video_script":
            return self.format_video_script(parsed_output)
        if canonical_type == "ad_copy":
            return self.format_ad_copy(parsed_output)
        return self.format_campaign_asset(parsed_output)

    def format_instagram_post(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Format an Instagram post output."""

        contract = get_output_contract("instagram_post")
        return self._format_with_contract(parsed_output, contract)

    def format_instagram_reel(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Format an Instagram reel output."""

        contract = get_output_contract("instagram_reel")
        return self._format_with_contract(parsed_output, contract)

    def format_property_description(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Format a property description output."""

        contract = get_output_contract("property_description")
        return self._format_with_contract(parsed_output, contract)

    def format_image_prompt(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Format an image prompt output."""

        contract = get_output_contract("image_prompt")
        return self._format_with_contract(parsed_output, contract)

    def format_video_prompt(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Format a video prompt output."""

        contract = get_output_contract("video_prompt")
        return self._format_with_contract(parsed_output, contract)

    def format_video_script(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Format a video script output."""

        contract = get_output_contract("video_script")
        return self._format_with_contract(parsed_output, contract)

    def format_ad_copy(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Format an ad copy output."""

        contract = get_output_contract("ad_copy")
        return self._format_with_contract(parsed_output, contract)

    def format_campaign_asset(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Format a campaign asset output."""

        contract = get_output_contract("campaign_asset")
        return self._format_with_contract(parsed_output, contract)

    def _format_with_contract(self, parsed_output: dict[str, Any], contract: Any) -> dict[str, Any]:
        """Apply a contract and preserve formatting diagnostics."""

        raw_content = self._extract_raw_content(parsed_output)
        source = self._extract_source_payload(parsed_output)
        normalized_source = self._normalize_source(source, contract.aliases)
        output = dict(contract.defaults)
        warnings: list[str] = []

        for field_name in contract.required_fields + contract.optional_fields:
            if field_name in normalized_source:
                output[field_name] = self._coerce_field_value(field_name, normalized_source[field_name])

        for field_name, value in normalized_source.items():
            canonical = contract.aliases.get(field_name, field_name)
            if canonical in output and output.get(canonical) in ("", [], None):
                output[canonical] = self._coerce_field_value(canonical, value)

        extracted = self._extract_from_text(raw_content, contract.content_type)
        for field_name, value in extracted.items():
            if field_name in output and output.get(field_name) in ("", [], None):
                output[field_name] = value

        if contract.content_type == "instagram_post":
            output = self._normalize_instagram_post_output(output, raw_content)
        if contract.content_type == "video_script":
            output = self._normalize_video_script_output(output, raw_content)

        missing_required = [field for field in contract.required_fields if self._is_empty(output.get(field))]
        if missing_required:
            warnings.append(f"Missing required formatted fields: {', '.join(missing_required)}")

        output["raw_content"] = raw_content
        output["missing_required_fields"] = missing_required
        output["formatting_warnings"] = warnings
        output["content_type"] = contract.content_type
        return output

    def _normalize_instagram_post_output(self, output: dict[str, Any], raw_content: str) -> dict[str, Any]:
        """Ensure Instagram posts always carry hook, caption, CTA, and hashtags."""

        caption_source = normalize_markdown_content(raw_content or str(output.get("caption", "")))
        hook = output.get("hook")
        if self._is_empty(hook):
            output["hook"] = self._extract_first_sentence(caption_source) or caption_source

        if self._is_empty(output.get("caption")):
            output["caption"] = caption_source

        if self._is_empty(output.get("cta")):
            detected_cta = self._detect_cta(caption_source)
            output["cta"] = detected_cta or "Contact our team to learn more."

        hashtags = output.get("hashtags")
        if self._is_empty(hashtags):
            output["hashtags"] = self._extract_hashtags(caption_source)

        return output

    def _extract_source_payload(self, parsed_output: dict[str, Any]) -> dict[str, Any]:
        """Prefer JSON payloads while keeping raw content available."""

        source = parsed_output.get("json")
        if isinstance(source, dict):
            return dict(source)

        content = parsed_output.get("content")
        if isinstance(content, dict):
            return dict(content)

        if isinstance(content, str):
            candidate = self._try_parse_json(content)
            if isinstance(candidate, dict):
                return candidate

        return {}

    def _normalize_source(self, source: dict[str, Any], aliases: dict[str, str]) -> dict[str, Any]:
        """Map aliases to canonical field names."""

        normalized: dict[str, Any] = {}
        for key, value in source.items():
            canonical = aliases.get(key, key)
            normalized[canonical] = value
        return normalized

    def _extract_from_text(self, text: str, content_type: str) -> dict[str, Any]:
        """Extract structured fields from raw text when JSON is unavailable."""

        if not text:
            return {}

        normalized_text = normalize_markdown_content(text)
        sections = self._split_labelled_sections(normalized_text)
        if content_type == "instagram_post":
            return {
                "hook": sections.get("hook", ""),
                "caption": sections.get("caption", normalized_text),
                "cta": sections.get("cta", ""),
                "hashtags": self._extract_hashtags(normalized_text),
                "notes": sections.get("notes", ""),
            }
        if content_type == "instagram_reel":
            return {
                "hook": sections.get("hook", ""),
                "script": sections.get("script", sections.get("caption", normalized_text)),
                "scene_direction": sections.get("scene_direction", sections.get("scene", "")),
                "cta": sections.get("cta", ""),
                "hashtags": self._extract_hashtags(normalized_text),
                "notes": sections.get("notes", ""),
            }
        if content_type == "property_description":
            return {
                "title": sections.get("title", sections.get("headline", "")),
                "description": sections.get("description", sections.get("long_description", sections.get("short_description", sections.get("summary", normalized_text)))),
                "highlights": self._extract_list_like(sections.get("highlights", sections.get("features", ""))),
                "cta": sections.get("cta", ""),
                "notes": sections.get("notes", ""),
            }
        if content_type == "image_prompt":
            return {
                "image_prompt": sections.get("image_prompt", sections.get("prompt", sections.get("visual_direction", sections.get("visual", normalized_text)))),
                "style": sections.get("style", sections.get("visual_style", "")),
                "camera": sections.get("camera", sections.get("camera_direction", "")),
                "lighting": sections.get("lighting", ""),
                "negative_prompt": sections.get("negative_prompt", ""),
                "notes": sections.get("notes", ""),
            }
        if content_type == "video_prompt":
            return {
                "scene_description": sections.get("scene_description", sections.get("scene", normalized_text)),
                "camera_motion": sections.get("camera_motion", sections.get("motion", "")),
                "mood": sections.get("mood", ""),
                "sequence": self._extract_list_like(sections.get("sequence", "")),
                "voiceover_direction": sections.get("voiceover_direction", sections.get("voiceover", "")),
                "notes": sections.get("notes", ""),
            }
        if content_type == "video_script":
            scene_1 = sections.get("scene_1", sections.get("scene1", sections.get("scene", sections.get("script", normalized_text))))
            scene_2 = sections.get("scene_2", sections.get("scene2", ""))
            scene_3 = sections.get("scene_3", sections.get("scene3", ""))
            return {
                "hook": sections.get("hook", self._extract_first_sentence(normalized_text)),
                "scene_1": scene_1,
                "scene_2": scene_2,
                "scene_3": scene_3,
                "voiceover": sections.get("voiceover", sections.get("voiceover_direction", "")),
                "cta": sections.get("cta", self._detect_cta(normalized_text)),
                "script": sections.get("script", normalized_text),
                "music_mood": sections.get("music_mood", sections.get("mood", "")),
                "scene_sequence": self._extract_list_like(sections.get("scene_sequence", sections.get("scenes", ""))),
                "storyboard": self._extract_list_like(sections.get("storyboard", "")),
                "camera_direction": sections.get("camera_direction", sections.get("camera", "")),
                "notes": sections.get("notes", ""),
            }
        if content_type == "ad_copy":
            return {
                "headline": sections.get("headline", sections.get("hook", sections.get("title", ""))),
                "primary_text": sections.get("primary_text", sections.get("primarytext", sections.get("body_copy", sections.get("copy", normalized_text)))),
                "description": sections.get("description", sections.get("summary", "")),
                "cta": sections.get("cta", self._detect_cta(normalized_text)),
                "notes": sections.get("notes", ""),
            }
        return {
            "campaign_name": sections.get("campaign_name", sections.get("name", "")),
            "objective": sections.get("objective", ""),
            "main_message": sections.get("main_message", sections.get("message", normalized_text)),
            "assets": self._extract_list_like(sections.get("assets", sections.get("resources", ""))),
            "cta": sections.get("cta", ""),
            "notes": sections.get("notes", ""),
        }

    def _split_labelled_sections(self, text: str) -> dict[str, str]:
        """Split text by common label patterns."""

        sections: dict[str, str] = {}
        if not text:
            return sections

        lines = text.split("\n")
        current_label: str | None = None
        buffer: list[str] = []

        def flush() -> None:
            nonlocal buffer, current_label
            if current_label is not None:
                sections[current_label] = "\n".join(buffer).strip()
            buffer = []

        for line in lines:
            match = re.match(r"^\s*(hook|caption|cta|notes|script|title|headline|primary_text|primarytext|summary|description|short_description|long_description|highlights|features|image_prompt|prompt|visual_direction|visual|style|camera|camera_direction|lighting|negative_prompt|scene_1|scene_2|scene_3|scene1|scene2|scene3|scene_description|scene|camera_motion|motion|mood|music_mood|sequence|voiceover_direction|voiceover|scene_sequence|storyboard|campaign_name|name|objective|main_message|message|assets|resources)\s*[:\-]\s*(.*)$", line, flags=re.IGNORECASE)
            if match:
                flush()
                current_label = match.group(1).lower()
                buffer = [match.group(2).strip()]
                continue
            if current_label is not None:
                buffer.append(line)
        flush()
        return sections

    def _extract_hashtags(self, text: str) -> list[str]:
        """Extract and normalize hashtags from text."""

        tags = {tag.lower() for tag in re.findall(r"#\w+", text or "")}
        return sorted(tags)

    def _extract_first_sentence(self, text: str) -> str:
        """Return the first meaningful sentence from a text block."""

        if not text:
            return ""
        sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]
        if not sentences:
            return ""
        return sentences[0]

    def _detect_cta(self, text: str) -> str:
        """Detect a CTA from plain text when one is not explicitly labeled."""

        if not text:
            return ""
        labelled = self._split_labelled_sections(text).get("cta", "")
        if labelled:
            return labelled.strip()

        cta_patterns = (
            r"([^.!?]*(?:contact|message|dm|learn more|book|request|speak with|get in touch|inquire|enquire)[^.!?]*[.!?])",
            r"([^.!?]*(?:contact|message|dm|learn more|book|request|speak with|get in touch|inquire|enquire)[^.!?]*)$",
        )
        for pattern in cta_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_list_like(self, value: str) -> list[str]:
        """Convert common list-like text into a list of strings."""

        if not value:
            return []
        parts = [part.strip(" -•\t") for part in re.split(r"[\n,;]+", value) if part.strip(" -•\t")]
        return parts

    def _try_parse_json(self, text: str) -> Any:
        """Try to parse a JSON string."""

        candidate = text.strip()
        if not candidate:
            return None
        if candidate.startswith("```"):
            candidate = re.sub(r"^```(?:json)?\s*", "", candidate, flags=re.IGNORECASE)
            candidate = re.sub(r"\s*```$", "", candidate)
        try:
            return json.loads(candidate)
        except Exception:
            return None

    def _coerce_field_value(self, field_name: str, value: Any) -> Any:
        """Normalize a field value based on its target type."""

        if field_name in {"scene_sequence", "storyboard"}:
            if isinstance(value, list):
                return [item if isinstance(item, dict) else str(item).strip() for item in value if str(item).strip() or isinstance(item, dict)]
            if isinstance(value, str):
                return self._extract_list_like(value)
            if isinstance(value, dict):
                return [dict(value)]
            return [str(value).strip()] if str(value).strip() else []
        if field_name == "camera_direction":
            if isinstance(value, dict):
                return dict(value)
            return str(value).strip()
        if field_name in {"hashtags", "highlights", "sequence", "assets"}:
            if isinstance(value, list):
                return [str(item).strip() for item in value if str(item).strip()]
            if isinstance(value, str):
                return self._extract_list_like(value)
            return [str(value).strip()] if str(value).strip() else []
        if value is None:
            return ""
        return str(value).strip()

    def _normalize_video_script_output(self, output: dict[str, Any], raw_content: str) -> dict[str, Any]:
        """Ensure video scripts expose the new reel-friendly schema."""

        script_source = normalize_markdown_content(raw_content or str(output.get("script", "")))
        scene_sequence = output.get("scene_sequence") or []
        if self._is_empty(output.get("scene_1")):
            first_scene = ""
            if isinstance(scene_sequence, list) and scene_sequence:
                first_scene = self._stringify(scene_sequence[0])
            output["scene_1"] = first_scene or self._extract_first_sentence(script_source) or script_source
        if self._is_empty(output.get("scene_2")) and isinstance(scene_sequence, list) and len(scene_sequence) > 1:
            output["scene_2"] = self._stringify(scene_sequence[1])
        if self._is_empty(output.get("scene_3")) and isinstance(scene_sequence, list) and len(scene_sequence) > 2:
            output["scene_3"] = self._stringify(scene_sequence[2])
        if self._is_empty(output.get("scene_2")):
            output["scene_2"] = self._extract_first_sentence(script_source) if script_source else ""
        if self._is_empty(output.get("scene_3")):
            output["scene_3"] = self._detect_cta(script_source) or output.get("cta", "")
        if self._is_empty(output.get("voiceover")):
            output["voiceover"] = self._detect_cta(script_source) or output.get("scene_1", "")
        if self._is_empty(output.get("cta")):
            output["cta"] = self._detect_cta(script_source) or "Contact our team to learn more."
        return output

    def _extract_raw_content(self, parsed_output: dict[str, Any]) -> str:
        """Return the raw content if available."""

        raw_content = parsed_output.get("raw_content")
        if isinstance(raw_content, str):
            return raw_content
        content = parsed_output.get("content")
        if isinstance(content, str):
            return content
        return ""

    def _is_empty(self, value: Any) -> bool:
        """Return whether a formatted field is empty."""

        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        if isinstance(value, list):
            return len(value) == 0
        return False

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
