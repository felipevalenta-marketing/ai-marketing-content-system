"""Structured result helpers for the content generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PipelineResult:
    """Reusable pipeline result container."""

    success: bool
    brand: str
    platform: str
    content_type: str
    input_request: dict[str, Any]
    context_summary: dict[str, Any]
    prompt_payload: dict[str, Any] | None
    ai_response: dict[str, Any] | None
    parsed_output: dict[str, Any] | None
    metadata: dict[str, Any]
    error: str | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result into a JSON-friendly dictionary."""

        return {
            "success": self.success,
            "brand": self.brand,
            "platform": self.platform,
            "content_type": self.content_type,
            "input_request": self.input_request,
            "context_summary": self.context_summary,
            "prompt_payload": self.prompt_payload,
            "ai_response": self.ai_response,
            "parsed_output": self.parsed_output,
            "metadata": self.metadata,
            "error": self.error,
            "warnings": self.warnings,
        }


def build_success_result(
    brand: str,
    platform: str,
    content_type: str,
    input_request: dict[str, Any],
    context_summary: dict[str, Any],
    prompt_payload: dict[str, Any],
    ai_response: dict[str, Any],
    parsed_output: dict[str, Any],
    metadata: dict[str, Any],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build a successful pipeline response."""

    return PipelineResult(
        success=True,
        brand=brand,
        platform=platform,
        content_type=content_type,
        input_request=input_request,
        context_summary=context_summary,
        prompt_payload=prompt_payload,
        ai_response=ai_response,
        parsed_output=parsed_output,
        metadata=metadata,
        error=None,
        warnings=warnings or [],
    ).to_dict()


def build_failure_result(
    brand: str,
    platform: str,
    content_type: str,
    input_request: dict[str, Any],
    context_summary: dict[str, Any],
    metadata: dict[str, Any],
    error: str,
    prompt_payload: dict[str, Any] | None = None,
    ai_response: dict[str, Any] | None = None,
    parsed_output: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build a failure pipeline response."""

    return PipelineResult(
        success=False,
        brand=brand,
        platform=platform,
        content_type=content_type,
        input_request=input_request,
        context_summary=context_summary,
        prompt_payload=prompt_payload,
        ai_response=ai_response,
        parsed_output=parsed_output,
        metadata=metadata,
        error=error,
        warnings=warnings or [],
    ).to_dict()
