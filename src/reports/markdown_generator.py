"""Generate human-readable markdown reports from structured results."""

from __future__ import annotations

from typing import Any

from src.reports.markdown_contracts import (
    MarkdownReportRequestContract,
    MarkdownReportResultContract,
    MarkdownSectionContract,
    SUPPORTED_MARKDOWN_REPORT_TYPES,
)
from src.reports.markdown_exporter import MarkdownExporter
from src.reports.markdown_renderer import render_report
from src.reports.markdown_sections import (
    build_asset_section,
    build_campaign_section,
    build_context_section,
    build_cost_usage_section,
    build_creative_direction_section,
    build_errors_section,
    build_executive_summary_section,
    build_generation_output_section,
    build_governance_section,
    build_metadata_section,
    build_media_section,
    build_storage_section,
    build_tracking_section,
    build_title_section,
    build_token_usage_section,
    build_warnings_section,
    build_workflow_snapshot_section,
    build_workflow_summary_section,
)
from src.reports.markdown_result import build_failure_result, build_success_result, build_validation_failure_result
from src.reports.markdown_templates import get_markdown_template
from src.reports.markdown_validator import MarkdownValidator
from src.reports.markdown_utils import safe_dict, safe_list, safe_text, utc_now_iso
from src.utils.logger import get_logger, log_warning


SECTION_BUILDERS = {
    "title": build_title_section,
    "executive_summary": build_executive_summary_section,
    "context": build_context_section,
    "workflow_summary": build_workflow_summary_section,
    "workflow_snapshot": build_workflow_snapshot_section,
    "generation_output": build_generation_output_section,
    "campaign": build_campaign_section,
    "assets": build_asset_section,
    "creative_direction": build_creative_direction_section,
    "media": build_media_section,
    "governance": build_governance_section,
    "token_usage": build_token_usage_section,
    "cost_usage": build_cost_usage_section,
    "storage": build_storage_section,
    "tracking": build_tracking_section,
    "warnings": build_warnings_section,
    "errors": build_errors_section,
    "metadata": build_metadata_section,
}


class MarkdownReportGenerator:
    """Turn structured analytics and workflow payloads into markdown."""

    def __init__(self, output_root: str = "outputs/reports/markdown", logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.exporter = MarkdownExporter(output_root=output_root, logger=self.logger)
        self.validator = MarkdownValidator()
        self.output_root = output_root

    def generate_report(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate a markdown report from structured data."""

        payload = self._normalize_payload(data)
        requested_report_type = safe_text(payload.get("report_type"), limit=80).strip().lower()
        report_type = self._resolve_report_type(payload)
        template = get_markdown_template(report_type)
        title = safe_text(payload.get("title") or template.get("name") or "Report", limit=160) or "Report"
        generated_at = utc_now_iso()
        metadata = self._build_metadata(payload, report_type, title, generated_at=generated_at)
        sections: list[str] = []
        section_records: list[dict[str, Any]] = []
        for order, section_id in enumerate(template.get("sections", [])):
            builder = SECTION_BUILDERS.get(section_id)
            if builder is None:
                continue
            content = builder(payload)
            if not safe_text(content, limit=500000):
                continue
            sections.append(content)
            section_records.append(MarkdownSectionContract(section_id=section_id, title=section_id.replace("_", " ").title(), content=content, order=order, present=True).to_dict())

        if not sections:
            fallback_section = "No structured markdown content was available."
            fallback = render_report(title, [fallback_section])
            sections = [fallback_section]
            section_records.append(
                MarkdownSectionContract(
                    section_id="executive_summary",
                    title="Executive Summary",
                    content=fallback_section,
                    order=0,
                    present=True,
                ).to_dict()
            )
            markdown = fallback
        else:
            markdown = render_report(title, sections)

        export_path = ""
        export_result: dict[str, Any] = {}
        if self._should_export(payload):
            export_result = self.exporter.export_markdown(markdown, metadata=metadata, overwrite=bool(payload.get("overwrite", False)))
            export_path = safe_text(export_result.get("path"), limit=260)
            metadata["report_index_path"] = safe_text(export_result.get("index_path"), limit=260)
            metadata["report_id"] = safe_text(export_result.get("report_id"), limit=120)

        validation_payload = {
            "report_type": report_type,
            "title": title,
            "markdown": markdown,
            "export_path": export_path,
            "metadata": metadata,
        }
        validation = self.validator.validate(validation_payload)
        warnings = list(dict.fromkeys(safe_list(payload.get("warnings")) + safe_list(validation.get("warnings")) + safe_list(export_result.get("warnings"))))
        errors = list(dict.fromkeys(safe_list(validation.get("errors")) + safe_list(export_result.get("errors"))))
        if requested_report_type and requested_report_type not in SUPPORTED_MARKDOWN_REPORT_TYPES:
            warnings.append(f"Unsupported report_type '{requested_report_type}' was normalized to a supported template.")
        result = build_success_result(
            report_type=report_type,
            title=title,
            markdown=markdown,
            sections=section_records,
            word_count=self._word_count(markdown),
            export_path=export_path,
            metadata=metadata,
            warnings=list(dict.fromkeys([safe_text(item, limit=240) for item in warnings if safe_text(item, limit=240)])),
            errors=list(dict.fromkeys([safe_text(item, limit=240) for item in errors if safe_text(item, limit=240)])),
        )
        if errors:
            result["success"] = False
        result["validation"] = validation
        result["export"] = export_result
        result["generated_at"] = generated_at
        result["report_id"] = metadata.get("report_id", "")
        result["report_index_path"] = metadata.get("report_index_path", "")
        return result

    def generate_workflow_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.generate_report({**data, "report_type": "workflow_report"})

    def generate_campaign_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.generate_report({**data, "report_type": "campaign_report"})

    def generate_generation_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.generate_report({**data, "report_type": "generation_report"})

    def generate_asset_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.generate_report({**data, "report_type": "asset_report"})

    def generate_governance_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.generate_report({**data, "report_type": "governance_report"})

    def generate_tracking_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.generate_report({**data, "report_type": "tracking_report"})

    def generate_cost_report(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.generate_report({**data, "report_type": "cost_report"})

    def generate_executive_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        return self.generate_report({**data, "report_type": "executive_summary"})

    def build_result(self, **kwargs: Any) -> dict[str, Any]:
        return build_success_result(**kwargs)

    def _normalize_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        payload = dict(data or {})
        reporting = safe_dict(payload.get("reporting"))
        if reporting:
            payload = {**reporting, **payload}
        for key in ("workflow_result", "pipeline_result", "campaign_result", "asset_result", "governance_result", "token_summary", "cost_summary", "storage_summary"):
            if key in payload:
                payload[key] = safe_dict(payload.get(key))
        if not payload.get("title"):
            payload["title"] = self._default_title(payload)
        return payload

    def _resolve_report_type(self, payload: dict[str, Any]) -> str:
        explicit = safe_text(payload.get("report_type"), limit=80).strip().lower()
        if explicit in SUPPORTED_MARKDOWN_REPORT_TYPES:
            return explicit
        workflow = safe_dict(payload.get("workflow_result") or payload.get("workflow_state") or payload.get("workflow_snapshot"))
        workflow_history = safe_list(payload.get("workflow_state_history") or payload.get("workflow_timeline"))
        if workflow and (workflow.get("timeline") or workflow.get("history") or workflow.get("status_transitions") or safe_dict(workflow.get("state"))):
            return "workflow_report"
        if workflow_history:
            return "workflow_report"
        if payload.get("image_prompt_validation") and not payload.get("image_prompt_result"):
            return "image_prompt_validation_report"
        if payload.get("image_prompt_result"):
            return "image_prompt_report"
        if payload.get("video_prompt_result"):
            return "video_prompt_report"
        if payload.get("video_script_result"):
            return "video_script_report"
        if payload.get("storyboard"):
            return "storyboard_report"
        if safe_dict(payload.get("video_script_result")).get("storyboard"):
            return "storyboard_report"
        if payload.get("visual_identity") or payload.get("color_palette") or payload.get("moodboard"):
            return "visual_style_report"
        if payload.get("creative_direction_result"):
            return "creative_direction_report"
        if payload.get("asset_coordination_result") or payload.get("asset_plan"):
            return "asset_report"
        if payload.get("campaign_result") or payload.get("campaign_type"):
            return "campaign_report"
        if payload.get("workflow_result") or payload.get("workflow_id") or payload.get("workflow_type"):
            return "workflow_report"
        if payload.get("workflow_state") or payload.get("workflow_snapshot"):
            return "workflow_report"
        if payload.get("cost_usage"):
            return "cost_report"
        if payload.get("token_usage"):
            return "tracking_report"
        if payload.get("governance_result"):
            return "governance_report"
        if payload.get("consolidated_report") or payload.get("execution_report") or payload.get("formatted_output") or payload.get("parsed_output"):
            return "execution_report"
        return "executive_summary"

    def _default_title(self, payload: dict[str, Any]) -> str:
        report_type = self._resolve_report_type(payload)
        template = get_markdown_template(report_type)
        return safe_text(template.get("name") or "Report", limit=160)

    def _should_export(self, payload: dict[str, Any]) -> bool:
        return bool(payload.get("export_markdown_report") or payload.get("export_markdown") or payload.get("markdown_export"))

    def _build_metadata(self, payload: dict[str, Any], report_type: str, title: str, generated_at: str | None = None) -> dict[str, Any]:
        metadata = safe_dict(payload.get("metadata"))
        generated_value = generated_at or utc_now_iso()
        report_id = self._build_report_id(payload, report_type, title, generated_value)
        return {
            "brand": safe_text(payload.get("brand") or metadata.get("brand"), limit=80),
            "platform": safe_text(payload.get("platform") or metadata.get("platform"), limit=80),
            "campaign_type": safe_text(payload.get("campaign_type") or metadata.get("campaign_type"), limit=80),
            "content_type": safe_text(payload.get("content_type") or metadata.get("content_type"), limit=80),
            "report_type": report_type,
            "title": title,
            "output_root": self.output_root,
            "workflow_id": safe_text(payload.get("workflow_id") or metadata.get("workflow_id"), limit=120),
            "workflow_type": safe_text(payload.get("workflow_type") or metadata.get("workflow_type"), limit=120),
            "storage_root": safe_text((safe_dict(payload.get("storage_summary"))).get("storage_root"), limit=260),
            "generated_at": generated_value,
            "report_id": report_id,
        }

    def _word_count(self, markdown: str) -> int:
        return len([word for word in safe_text(markdown, limit=1000000).split() if word])

    def _build_report_id(self, payload: dict[str, Any], report_type: str, title: str, generated_at: str) -> str:
        brand = safe_text(payload.get("brand") or safe_dict(payload.get("metadata")).get("brand"), limit=80) or "unknown_brand"
        safe_generated = generated_at.replace(":", "-").replace("+", "_")
        return safe_text(f"{brand}_{report_type}_{title}_{safe_generated}", limit=120)


def build_failure(**kwargs: Any) -> dict[str, Any]:
    return build_failure_result(**kwargs)


def build_validation_failure(**kwargs: Any) -> dict[str, Any]:
    return build_validation_failure_result(**kwargs)
