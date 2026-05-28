"""Normalize and structure raw LLM responses."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any

from src.utils.file_utils import normalize_markdown_content
from src.utils.logger import get_logger, log_warning


@dataclass(frozen=True)
class ParsedTextResponse:
    """Structured parser output."""

    content: str
    hashtags: list[str]
    cta: str | None
    json: dict[str, Any] | None
    raw_content: str
    parser_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the parsed response."""

        return {
            "content": self.content,
            "hashtags": self.hashtags,
            "cta": self.cta,
            "json": self.json,
            "raw_content": self.raw_content,
            "parser_warnings": self.parser_warnings,
        }


class ResponseParser:
    """Parse model output into a predictable structure."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)

    def parse_text_response(self, response: dict[str, Any]) -> dict[str, Any]:
        """Parse a generation response into normalized content."""

        warnings: list[str] = []
        content = self._extract_content(response)
        normalized = normalize_markdown_content(content)
        if not normalized.strip():
            warnings.append("Empty model content received.")
            log_warning(self.logger, warnings[-1])
            return ParsedTextResponse(
                content="",
                hashtags=[],
                cta=None,
                json=None,
                raw_content=self._extract_raw_content(response),
                parser_warnings=warnings,
            ).to_dict()

        json_candidate = self._clean_json_candidate(normalized)
        parsed_json = self.try_parse_json(normalized)
        hashtags = self.extract_hashtags(normalized)
        cta = self.extract_cta(normalized)

        if json_candidate and parsed_json is None:
            warnings.append("Malformed JSON-like content received.")
        if parsed_json is None and normalized != content:
            warnings.append("Content normalized before parsing.")
        if parsed_json is None and not hashtags and not cta:
            warnings.append("Parser returned plain text fallback.")

        return ParsedTextResponse(
            content=normalized,
            hashtags=hashtags,
            cta=cta,
            json=parsed_json,
            raw_content=self._extract_raw_content(response) or content,
            parser_warnings=warnings,
        ).to_dict()

    def extract_hashtags(self, text: str) -> list[str]:
        """Extract hashtags from text."""

        tags = {tag.lower() for tag in re.findall(r"#\w+", text or "")}
        return sorted(tags)

    def extract_cta(self, text: str) -> str | None:
        """Extract a CTA from text when present."""

        if not text:
            return None

        label_match = re.search(r"^(?:cta|call to action)\s*[:\-]\s*(.+)$", text, flags=re.IGNORECASE | re.MULTILINE)
        if label_match:
            return label_match.group(1).strip() or None

        last_sentence = re.split(r"(?<=[.!?])\s+", text.strip())[-1].strip()
        if last_sentence:
            return last_sentence
        return None

    def try_parse_json(self, text: str) -> dict[str, Any] | None:
        """Try to parse JSON from text and fail gracefully."""

        candidate = self._clean_json_candidate(text)
        if not candidate:
            return None

        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            return None

        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            return {"items": parsed}
        return {"value": parsed}

    def _extract_content(self, response: dict[str, Any]) -> str:
        """Extract the textual content from a client response."""

        content = response.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(str(item) for item in content)

        raw_response = response.get("raw_response")
        if isinstance(raw_response, dict):
            raw_content = raw_response.get("content")
            if isinstance(raw_content, str):
                return raw_content
        return str(content or "")

    def _extract_raw_content(self, response: dict[str, Any]) -> str:
        """Extract the raw model content from the response payload."""

        raw_response = response.get("raw_response")
        if isinstance(raw_response, dict):
            raw_content = raw_response.get("content")
            if isinstance(raw_content, str):
                return raw_content
        content = response.get("content")
        return content if isinstance(content, str) else str(content or "")

    def _clean_json_candidate(self, text: str) -> str:
        """Remove markdown fences and isolate likely JSON."""

        if not text:
            return ""

        fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, flags=re.IGNORECASE | re.DOTALL)
        if fenced:
            return fenced.group(1).strip()

        stripped = text.strip()
        if stripped.startswith("{") and stripped.endswith("}"):
            return stripped
        if stripped.startswith("[") and stripped.endswith("]"):
            return stripped

        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            return stripped[start : end + 1]
        return ""
