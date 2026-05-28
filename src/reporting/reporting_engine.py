"""Orchestrate report building, rendering, and export."""

from __future__ import annotations

from typing import Any

from src.reporting.report_builder import ReportBuilder
from src.reporting.report_exporter import ReportExporter
from src.reporting.report_renderer import ReportRenderer
from src.reporting.report_metrics import safe_dict, safe_list, safe_text
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
            "rendered": rendered,
            "rendered_markdown": rendered_markdown,
            "rendered_text": rendered_text,
            "exported_files": exported_files,
            "warnings": self._collect_warnings(reports),
            "errors": self._collect_errors(reports),
            "metadata": {
                "brand": self._extract_brand(payload),
                "report_name": report_name or safe_text(consolidated.get("title", "report"), limit=80),
                "export_enabled": export,
                "formats": list(formats or ["markdown", "json"]),
                "report_types": list(reports.keys()),
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
