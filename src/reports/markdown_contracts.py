"""Contracts for markdown report generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""

    return datetime.now(timezone.utc).isoformat()


SUPPORTED_MARKDOWN_REPORT_TYPES = (
    "execution_report",
    "workflow_report",
    "campaign_report",
    "generation_report",
    "asset_report",
    "governance_report",
    "tracking_report",
    "cost_report",
    "storage_report",
    "creative_direction_report",
    "media_report",
    "image_prompt_report",
    "image_prompt_validation_report",
    "visual_style_report",
    "storyboard_report",
    "video_script_report",
    "video_prompt_report",
    "executive_summary",
    "client_presentation_report",
    "pdf_export_report",
    "dashboard_report",
    "audit_report",
    "performance_report",
    "monthly_usage_report",
)


@dataclass(frozen=True)
class MarkdownReportRequestContract:
    """Describe the input structure for markdown generation."""

    report_type: str
    title: str
    brand: str
    platform: str
    campaign_type: str
    content_type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_type": self.report_type,
            "title": self.title,
            "brand": self.brand,
            "platform": self.platform,
            "campaign_type": self.campaign_type,
            "content_type": self.content_type,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class MarkdownSectionContract:
    """Describe a rendered markdown section."""

    section_id: str
    title: str
    content: str
    order: int = 0
    present: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "title": self.title,
            "content": self.content,
            "order": self.order,
            "present": self.present,
        }


@dataclass(frozen=True)
class MarkdownReportResultContract:
    """Describe a markdown report output."""

    success: bool
    report_type: str
    title: str
    markdown: str
    sections: list[dict[str, Any]]
    word_count: int
    export_path: str
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "report_type": self.report_type,
            "title": self.title,
            "markdown": self.markdown,
            "sections": self.sections,
            "word_count": self.word_count,
            "export_path": self.export_path,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
            "generated_at": self.generated_at,
        }


@dataclass(frozen=True)
class MarkdownExportContract:
    """Describe a markdown export operation."""

    success: bool
    path: str
    markdown: str
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "path": self.path,
            "markdown": self.markdown,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }
