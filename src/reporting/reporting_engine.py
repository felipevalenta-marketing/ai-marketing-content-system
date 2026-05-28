"""Orchestrate report building, rendering, and export."""

from __future__ import annotations

from typing import Any

from src.reporting.report_builder import ReportBuilder
from src.reporting.report_exporter import ReportExporter
from src.reporting.report_renderer import ReportRenderer
from src.reporting.report_metrics import safe_dict, safe_float, safe_list, safe_text
from src.utils.logger import get_logger, log_context, log_warning


class ReportingEngine:
    """High-level analytics orchestration for execution results."""

    def __init__(self, output_root: str = "outputs/reports", logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.builder = ReportBuilder()
        self.renderer = ReportRenderer()
        self.exporter = ReportExporter(output_root=output_root, logger=self.logger)

    def generate(
        self,
        payload: dict[str, Any],
        export: bool = False,
        formats: list[str] | None = None,
        render_format: str = "terminal",
        report_name: str | None = None,
    ) -> dict[str, Any]:
        """Build, render, and optionally export a report bundle."""

        log_context(self.logger, "Building analytics reports")
        reports = self.builder.build_reports(payload)
        consolidated = reports["consolidated_report"]
        video_script_report = self._build_video_script_report(payload, reports["asset_report"])
        creative_direction_report = self._build_creative_direction_report(payload)
        rendered = self.renderer.render(consolidated, output_format=render_format)
        rendered_markdown = self.renderer.render_markdown(consolidated)
        rendered_text = self.renderer.render_terminal(consolidated)

        exported_files: dict[str, str] = {}
        if export:
            brand = self._extract_brand(payload)
            try:
                exported_files = self.exporter.export(consolidated, brand=brand, report_name=report_name, formats=formats)
            except Exception as exc:  # pragma: no cover - defensive fallback
                log_warning(self.logger, f"Report export failed: {exc}")
                exported_files = {}

        bundle = {
            "success": True,
            "execution_report": reports["execution_report"],
            "governance_report": reports["governance_report"],
            "campaign_report": reports["campaign_report"],
            "asset_report": reports["asset_report"],
            "export_report": reports["export_report"],
            "consolidated_report": consolidated,
            "image_prompt_report": self._build_image_prompt_report(payload, reports["asset_report"]),
            "video_script_report": video_script_report,
            "creative_direction_report": creative_direction_report,
            "rendered": rendered,
            "rendered_markdown": rendered_markdown,
            "rendered_text": rendered_text,
            "exported_files": exported_files,
            "warnings": self._collect_warnings({**reports, "video_script_report": video_script_report, "creative_direction_report": creative_direction_report}),
            "errors": self._collect_errors({**reports, "video_script_report": video_script_report, "creative_direction_report": creative_direction_report}),
            "metadata": {
                "brand": self._extract_brand(payload),
                "report_name": report_name or safe_text(consolidated.get("title", "report"), limit=80),
                "export_enabled": export,
                "formats": list(formats or ["markdown", "json"]),
            "report_types": list(reports.keys()) + ["image_prompt_report", "video_script_report", "creative_direction_report"],
            "image_prompt_metrics_present": self._has_image_prompt_data(payload),
            "video_script_metrics_present": self._has_video_script_data(payload),
            "creative_direction_metrics_present": self._has_creative_direction_data(payload),
            "token_metrics_present": self._has_token_data(payload),
        },
        }
        return bundle

    def build_execution_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build an execution report."""

        return self.builder.build_execution_report(payload)

    def build_governance_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build a governance report."""

        return self.builder.build_governance_report(payload)

    def build_campaign_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build a campaign report."""

        return self.builder.build_campaign_report(payload)

    def build_asset_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build an asset report."""

        return self.builder.build_asset_report(payload)

    def build_consolidated_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build a consolidated report."""

        return self.builder.build_consolidated_report(payload)

    def _extract_brand(self, payload: dict[str, Any]) -> str:
        metadata = safe_dict(payload.get("metadata"))
        return safe_text(payload.get("brand") or metadata.get("brand") or "", limit=80)

    def _collect_warnings(self, reports: dict[str, Any]) -> list[str]:
        warnings: list[str] = []
        for report in reports.values():
            if isinstance(report, dict):
                warnings.extend(safe_list(report.get("warnings")))
        return list(dict.fromkeys([safe_text(item, limit=240) for item in warnings if safe_text(item, limit=240)]))

    def _collect_errors(self, reports: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for report in reports.values():
            if isinstance(report, dict):
                errors.extend(safe_list(report.get("errors")))
        return list(dict.fromkeys([safe_text(item, limit=240) for item in errors if safe_text(item, limit=240)]))

    def _build_image_prompt_report(self, payload: dict[str, Any], asset_report: dict[str, Any]) -> dict[str, Any]:
        """Build a safe image prompt analytics snapshot when available."""

        image_prompt_result = safe_dict(payload.get("image_prompt_result"))
        image_prompt_validation = safe_dict(payload.get("image_prompt_validation"))
        if not image_prompt_result and not image_prompt_validation:
            return {}
        scores = safe_dict(image_prompt_validation.get("scores"))
        return {
            "image_type": safe_text(image_prompt_result.get("image_type") or payload.get("image_type") or "", limit=80),
            "visual_style_used": safe_text(image_prompt_result.get("visual_style") or payload.get("visual_style") or "", limit=80),
            "aspect_ratio": safe_text(image_prompt_result.get("aspect_ratio") or payload.get("aspect_ratio") or "", limit=80),
            "cinematic_rules_count": len(safe_list(image_prompt_result.get("cinematic_rules_applied"))),
            "negative_prompt_enabled": bool(image_prompt_result.get("negative_prompt")),
            "validation_status": bool(image_prompt_validation.get("valid", False)) if image_prompt_validation else False,
            "realism_score": safe_float(scores.get("realism"), 0.0),
            "completeness_score": safe_float(scores.get("completeness"), 0.0),
            "platform_fit_score": safe_float(scores.get("platform_fit"), 0.0),
            "conciseness_score": safe_float(scores.get("conciseness"), 0.0),
            "asset_report_reference": safe_dict(asset_report).get("summary", {}),
        }

    def _build_video_script_report(self, payload: dict[str, Any], asset_report: dict[str, Any]) -> dict[str, Any]:
        """Build a safe video script analytics snapshot when available."""

        video_script_result = safe_dict(payload.get("video_script_result"))
        video_script_validation = safe_dict(payload.get("video_script_validation"))
        if not video_script_result and not video_script_validation:
            return {}
        scores = safe_dict(video_script_validation.get("scores"))
        return {
            "video_type": safe_text(video_script_result.get("video_type") or payload.get("video_type") or "", limit=80),
            "duration": safe_text(video_script_result.get("duration") or payload.get("duration") or "", limit=80),
            "scene_count": len(safe_list(video_script_result.get("scene_sequence"))),
            "storyboard_scene_count": len(safe_list(video_script_result.get("storyboard"))),
            "voiceover_length": len(safe_text(video_script_result.get("voiceover") or "", limit=120).split()),
            "hook_present": bool(safe_text(video_script_result.get("hook") or "", limit=120)),
            "cta_present": bool(safe_text(video_script_result.get("cta") or "", limit=120)),
            "validation_status": bool(video_script_validation.get("valid", False)) if video_script_validation else False,
            "pacing_score": safe_float(scores.get("pacing"), 0.0),
            "factual_safety_score": safe_float(scores.get("factual_safety"), 0.0),
            "platform_fit_score": safe_float(scores.get("platform_fit"), 0.0),
            "asset_report_reference": safe_dict(asset_report).get("summary", {}),
        }

    def _build_creative_direction_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build a safe creative direction analytics snapshot when available."""

        creative_result = safe_dict(payload.get("creative_direction_result"))
        creative_validation = safe_dict(payload.get("creative_validation"))
        if not creative_result and not creative_validation:
            return {}
        scores = safe_dict(creative_validation.get("scores"))
        visual_identity = safe_dict(creative_result.get("visual_identity"))
        moodboard = safe_dict(creative_result.get("moodboard"))
        color_palette = safe_dict(creative_result.get("color_palette"))
        platform_guidelines = safe_dict(creative_result.get("platform_guidelines"))
        media_guidelines = safe_dict(creative_result.get("media_guidelines"))
        return {
            "creative_direction_type": safe_text(creative_result.get("creative_direction_type") or payload.get("creative_direction_type") or "", limit=80),
            "visual_identity_used": safe_text(visual_identity.get("name") or payload.get("visual_identity_used") or "", limit=80),
            "moodboard_rule_count": len(safe_list(moodboard.get("rules"))),
            "color_palette_used": safe_text(color_palette.get("name") or payload.get("color_palette_used") or "", limit=80),
            "platform_guideline_count": len(platform_guidelines),
            "media_guideline_count": len(media_guidelines),
            "creative_validation_status": bool(creative_validation.get("valid", False)) if creative_validation else False,
            "brand_fit_score": safe_float(scores.get("brand_fit"), 0.0),
            "realism_score": safe_float(scores.get("realism"), 0.0),
            "visual_consistency_score": safe_float(scores.get("visual_consistency"), 0.0),
        }

    def _has_image_prompt_data(self, payload: dict[str, Any]) -> bool:
        """Return whether the payload includes image prompt analytics data."""

        return bool(safe_dict(payload.get("image_prompt_result")) or safe_dict(payload.get("image_prompt_validation")))

    def _has_video_script_data(self, payload: dict[str, Any]) -> bool:
        """Return whether the payload includes video script analytics data."""

        return bool(safe_dict(payload.get("video_script_result")) or safe_dict(payload.get("video_script_validation")))

    def _has_creative_direction_data(self, payload: dict[str, Any]) -> bool:
        """Return whether the payload includes creative direction analytics data."""

        return bool(safe_dict(payload.get("creative_direction_result")) or safe_dict(payload.get("creative_validation")))

    def _has_token_data(self, payload: dict[str, Any]) -> bool:
        """Return whether the payload includes token tracking analytics data."""

        return bool(
            safe_dict(payload.get("token_usage"))
            or safe_dict(payload.get("execution_token_summary"))
            or safe_dict(payload.get("module_token_summary"))
            or safe_dict(payload.get("provider_token_summary"))
        )
