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
    formatted_output: dict[str, Any] | None
    validation_result: dict[str, Any] | None
    adaptation_result: dict[str, Any] | None
    platform_variants: dict[str, Any]
    governance_result: dict[str, Any] | None
    approval_status: str
    overall_quality_score: float | None
    governance_warnings: list[str]
    governance_errors: list[str]
    rendered_markdown: str | None
    rendered_text: str | None
    exported_files: dict[str, str]
    output_metadata: dict[str, Any]
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
            "formatted_output": self.formatted_output,
            "validation_result": self.validation_result,
            "adaptation_result": self.adaptation_result,
            "platform_variants": self.platform_variants,
            "governance_result": self.governance_result,
            "approval_status": self.approval_status,
            "overall_quality_score": self.overall_quality_score,
            "governance_warnings": self.governance_warnings,
            "governance_errors": self.governance_errors,
            "rendered_markdown": self.rendered_markdown,
            "rendered_text": self.rendered_text,
            "exported_files": self.exported_files,
            "output_metadata": self.output_metadata,
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
    formatted_output: dict[str, Any] | None,
    validation_result: dict[str, Any] | None,
    adaptation_result: dict[str, Any] | None,
    platform_variants: dict[str, Any] | None,
    governance_result: dict[str, Any] | None,
    approval_status: str,
    overall_quality_score: float | None,
    governance_warnings: list[str] | None,
    governance_errors: list[str] | None,
    rendered_markdown: str | None,
    rendered_text: str | None,
    exported_files: dict[str, str] | None,
    output_metadata: dict[str, Any] | None,
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
        formatted_output=formatted_output,
        validation_result=validation_result,
        adaptation_result=adaptation_result,
        platform_variants=platform_variants or {},
        governance_result=governance_result,
        approval_status=approval_status,
        overall_quality_score=overall_quality_score,
        governance_warnings=governance_warnings or [],
        governance_errors=governance_errors or [],
        rendered_markdown=rendered_markdown,
        rendered_text=rendered_text,
        exported_files=exported_files or {},
        output_metadata=output_metadata or {},
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
    formatted_output: dict[str, Any] | None = None,
    validation_result: dict[str, Any] | None = None,
    adaptation_result: dict[str, Any] | None = None,
    platform_variants: dict[str, Any] | None = None,
    governance_result: dict[str, Any] | None = None,
    approval_status: str = "unknown",
    overall_quality_score: float | None = None,
    governance_warnings: list[str] | None = None,
    governance_errors: list[str] | None = None,
    rendered_markdown: str | None = None,
    rendered_text: str | None = None,
    exported_files: dict[str, str] | None = None,
    output_metadata: dict[str, Any] | None = None,
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
        formatted_output=formatted_output,
        validation_result=validation_result,
        adaptation_result=adaptation_result,
        platform_variants=platform_variants or {},
        governance_result=governance_result,
        approval_status=approval_status,
        overall_quality_score=overall_quality_score,
        governance_warnings=governance_warnings or [],
        governance_errors=governance_errors or [],
        rendered_markdown=rendered_markdown,
        rendered_text=rendered_text,
        exported_files=exported_files or {},
        output_metadata=output_metadata or {},
        metadata=metadata,
        error=error,
        warnings=warnings or [],
    ).to_dict()
