"""Build standardized analytics reports from system outputs."""

from __future__ import annotations

from typing import Any

from src.reporting.asset_analytics import AssetAnalytics
from src.reporting.campaign_analytics import CampaignAnalytics
from src.reporting.execution_analytics import ExecutionAnalytics
from src.reporting.governance_analytics import GovernanceAnalytics
from src.reporting.report_contracts import (
    build_asset_report,
    build_campaign_report,
    build_consolidated_report,
    build_execution_report,
    build_export_report,
    build_governance_report,
)
from src.reporting.report_metrics import (
    safe_dict,
    safe_float,
    safe_int,
    safe_text,
    unique_strings,
)


class ReportBuilder:
    """Aggregate raw execution data into structured reports."""

    def __init__(self) -> None:
        self.execution_analytics = ExecutionAnalytics()
        self.governance_analytics = GovernanceAnalytics()
        self.campaign_analytics = CampaignAnalytics()
        self.asset_analytics = AssetAnalytics()

    def build_reports(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build all report variants from a source payload."""

        execution_metrics = self.execution_analytics.analyze(payload)
        governance_metrics = self.governance_analytics.analyze(payload)
        campaign_metrics = self.campaign_analytics.analyze(payload)
        asset_metrics = self.asset_analytics.analyze(payload)
        export_metrics = self._build_export_metrics(payload)

        execution_report = build_execution_report(
            summary=self._build_execution_summary(execution_metrics, payload),
            metrics=execution_metrics,
            warnings=self._collect_warnings(payload),
            errors=self._collect_errors(payload),
            metadata=self._build_common_metadata(payload),
            sections={
                "execution": execution_metrics,
                "pipeline": self._extract_pipeline_metrics(payload),
            },
        )
        governance_report = build_governance_report(
            summary=self._build_governance_summary(governance_metrics),
            metrics=governance_metrics,
            warnings=governance_metrics.get("warnings", []),
            errors=governance_metrics.get("errors", []),
            metadata=self._build_common_metadata(payload),
            sections={"checks": safe_dict(payload.get("governance_result", {})).get("checks", {})},
        )
        campaign_report = build_campaign_report(
            summary=self._build_campaign_summary(campaign_metrics),
            metrics=campaign_metrics,
            warnings=self._collect_campaign_warnings(payload),
            errors=self._collect_campaign_errors(payload),
            metadata=self._build_common_metadata(payload),
            sections={"strategy": safe_dict(payload.get("campaign_strategy", {})), "assets": safe_dict(payload.get("campaign_assets", {}))},
        )
        asset_report = build_asset_report(
            summary=self._build_asset_summary(asset_metrics),
            metrics=asset_metrics,
            warnings=self._collect_asset_warnings(payload),
            errors=self._collect_asset_errors(payload),
            metadata=self._build_common_metadata(payload),
            sections={"asset_plan": safe_dict(payload.get("asset_plan", {})), "asset_requirements": safe_dict(payload.get("asset_requirements", {}))},
        )
        export_report = build_export_report(
            summary=self._build_export_summary(export_metrics),
            metrics=export_metrics,
            warnings=self._collect_export_warnings(payload),
            errors=self._collect_export_errors(payload),
            metadata=self._build_common_metadata(payload),
            sections={"export_paths": self._extract_export_paths(payload)},
        )

        consolidated_sections = {
            "execution": execution_report,
            "governance": governance_report,
            "campaign": campaign_report,
            "asset": asset_report,
            "export": export_report,
        }
        consolidated_metrics = self._build_consolidated_metrics(
            execution_metrics,
            governance_metrics,
            campaign_metrics,
            asset_metrics,
            export_metrics,
        )
        consolidated_report = build_consolidated_report(
            summary=self._build_consolidated_summary(consolidated_metrics, payload),
            metrics=consolidated_metrics,
            warnings=self._merge_warning_lists(
                execution_report.get("warnings", []),
                governance_report.get("warnings", []),
                campaign_report.get("warnings", []),
                asset_report.get("warnings", []),
                export_report.get("warnings", []),
            ),
            errors=self._merge_warning_lists(
                execution_report.get("errors", []),
                governance_report.get("errors", []),
                campaign_report.get("errors", []),
                asset_report.get("errors", []),
                export_report.get("errors", []),
            ),
            metadata=self._build_common_metadata(payload),
            sections=consolidated_sections,
        )
        return {
            "execution_report": execution_report,
            "governance_report": governance_report,
            "campaign_report": campaign_report,
            "asset_report": asset_report,
            "export_report": export_report,
            "consolidated_report": consolidated_report,
        }

    def build_execution_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build the execution report only."""

        return self.build_reports(payload)["execution_report"]

    def build_governance_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build the governance report only."""

        return self.build_reports(payload)["governance_report"]

    def build_campaign_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build the campaign report only."""

        return self.build_reports(payload)["campaign_report"]

    def build_asset_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build the asset report only."""

        return self.build_reports(payload)["asset_report"]

    def build_consolidated_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Build the consolidated report only."""

        return self.build_reports(payload)["consolidated_report"]

    def _build_common_metadata(self, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = safe_dict(payload.get("metadata"))
        return {
            "brand": payload.get("brand") or metadata.get("brand", ""),
            "platform": payload.get("platform") or metadata.get("platform", ""),
            "content_type": payload.get("content_type") or metadata.get("content_type", ""),
            "objective": payload.get("objective") or metadata.get("objective", ""),
            "audience": payload.get("audience") or metadata.get("audience", ""),
            "location": payload.get("location") or metadata.get("location", ""),
            "provider": metadata.get("provider") or safe_dict(payload.get("ai_response")).get("provider", ""),
            "model": metadata.get("model") or safe_dict(payload.get("ai_response")).get("model", ""),
            "report_source": safe_text(payload.get("command") or "pipeline", limit=80),
        }

    def _build_execution_summary(self, metrics: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "success" if payload.get("success") else "failed",
            "execution_time_seconds": metrics.get("execution_time_seconds", 0.0),
            "stage_count": metrics.get("stage_count", 0),
            "warning_count": metrics.get("warning_count", 0),
            "error_count": metrics.get("error_count", 0),
        }

    def _build_governance_summary(self, metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": metrics.get("status", "unknown"),
            "approved": metrics.get("approved", False),
            "overall_score": metrics.get("overall_score", 0.0),
            "quality_score": metrics.get("quality_score", 0.0),
            "brand_score": metrics.get("brand_score", 0.0),
            "platform_score": metrics.get("platform_score", 0.0),
            "factual_safety_score": metrics.get("factual_safety_score", 0.0),
        }

    def _build_campaign_summary(self, metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "campaign_name": metrics.get("campaign_name", ""),
            "campaign_type": metrics.get("campaign_type", ""),
            "platform_count": metrics.get("platform_count", 0),
            "asset_count": metrics.get("asset_count", 0),
            "sequence_count": metrics.get("sequence_count", 0),
            "complexity": metrics.get("complexity", "low"),
        }

    def _build_asset_summary(self, metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "asset_count": metrics.get("asset_count", 0),
            "missing_asset_count": metrics.get("missing_asset_count", 0),
            "image_prompt_count": metrics.get("image_prompt_count", 0),
            "video_prompt_count": metrics.get("video_prompt_count", 0),
            "validation_valid": metrics.get("validation_valid", False),
        }

    def _build_export_summary(self, metrics: dict[str, Any]) -> dict[str, Any]:
        return {
            "exported": metrics.get("exported", False),
            "export_count": metrics.get("export_count", 0),
            "export_formats": metrics.get("export_formats", []),
        }

    def _build_consolidated_summary(self, metrics: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "success" if payload.get("success") else "failed",
            "report_count": metrics.get("report_count", 0),
            "warning_count": metrics.get("warning_count", 0),
            "error_count": metrics.get("error_count", 0),
            "execution_time_seconds": metrics.get("execution_time_seconds", 0.0),
        }

    def _build_export_metrics(self, payload: dict[str, Any]) -> dict[str, Any]:
        exported_files = safe_dict(payload.get("exported_files"))
        output_metadata = safe_dict(payload.get("output_metadata"))
        campaign_export_paths = safe_dict(payload.get("campaign_export_paths"))
        asset_export_paths = safe_dict(payload.get("asset_export_paths"))
        report_export_paths = safe_dict(payload.get("report_export_paths"))
        export_paths = self._extract_export_paths(payload)
        export_formats = list(export_paths.keys())
        return {
            "exported": bool(export_paths),
            "export_count": len(export_paths),
            "export_formats": export_formats,
            "output_export_count": len(exported_files),
            "campaign_export_count": len(campaign_export_paths),
            "asset_export_count": len(asset_export_paths),
            "report_export_count": len(report_export_paths),
            "validation_status": safe_text(output_metadata.get("validation_status", ""), limit=80),
        }

    def _build_consolidated_metrics(
        self,
        execution_metrics: dict[str, Any],
        governance_metrics: dict[str, Any],
        campaign_metrics: dict[str, Any],
        asset_metrics: dict[str, Any],
        export_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        warning_count = sum(
            safe_int(section.get("warning_count"), 0)
            for section in (execution_metrics, governance_metrics, campaign_metrics, asset_metrics, export_metrics)
        )
        error_count = sum(
            safe_int(section.get("error_count"), 0)
            for section in (execution_metrics, governance_metrics, campaign_metrics, asset_metrics, export_metrics)
        )
        return {
            "execution_time_seconds": safe_float(execution_metrics.get("execution_time_seconds"), 0.0),
            "warning_count": warning_count,
            "error_count": error_count,
            "report_count": 5,
            "governance_overall_score": safe_float(governance_metrics.get("overall_score"), 0.0),
            "campaign_complexity": safe_text(campaign_metrics.get("complexity", ""), limit=80),
            "asset_count": safe_int(asset_metrics.get("asset_count"), 0),
            "export_count": safe_int(export_metrics.get("export_count"), 0),
        }

    def _extract_pipeline_metrics(self, payload: dict[str, Any]) -> dict[str, Any]:
        metadata = safe_dict(payload.get("metadata"))
        execution = safe_dict(metadata.get("execution"))
        return {
            "started_at": execution.get("started_at", ""),
            "ended_at": execution.get("ended_at", ""),
            "duration_seconds": execution.get("duration_seconds", 0.0),
            "stages": safe_dict(execution.get("stages")),
        }

    def _extract_export_paths(self, payload: dict[str, Any]) -> dict[str, str]:
        export_paths: dict[str, str] = {}
        for key in ("exported_files", "campaign_export_paths", "asset_export_paths", "report_export_paths"):
            value = safe_dict(payload.get(key))
            for export_key, export_path in value.items():
                export_paths[safe_text(export_key, limit=80)] = safe_text(export_path, limit=260)
        return export_paths

    def _collect_warnings(self, payload: dict[str, Any]) -> list[str]:
        return unique_strings(payload.get("warnings", []))

    def _collect_errors(self, payload: dict[str, Any]) -> list[str]:
        return unique_strings(payload.get("errors", []))

    def _collect_campaign_warnings(self, payload: dict[str, Any]) -> list[str]:
        campaign_result = safe_dict(payload.get("campaign_result"))
        return unique_strings(campaign_result.get("warnings", []) + payload.get("warnings", []))

    def _collect_campaign_errors(self, payload: dict[str, Any]) -> list[str]:
        campaign_result = safe_dict(payload.get("campaign_result"))
        return unique_strings(campaign_result.get("errors", []) + payload.get("errors", []))

    def _collect_asset_warnings(self, payload: dict[str, Any]) -> list[str]:
        asset_result = safe_dict(payload.get("asset_coordination_result"))
        return unique_strings(asset_result.get("warnings", []) + payload.get("warnings", []))

    def _collect_asset_errors(self, payload: dict[str, Any]) -> list[str]:
        asset_result = safe_dict(payload.get("asset_coordination_result"))
        return unique_strings(asset_result.get("errors", []) + payload.get("errors", []))

    def _collect_export_warnings(self, payload: dict[str, Any]) -> list[str]:
        export_report = safe_dict(payload.get("report_export_paths"))
        return unique_strings(export_report.get("warnings", [])) if isinstance(export_report, dict) else []

    def _collect_export_errors(self, payload: dict[str, Any]) -> list[str]:
        export_report = safe_dict(payload.get("report_export_paths"))
        return unique_strings(export_report.get("errors", [])) if isinstance(export_report, dict) else []

    def _merge_warning_lists(self, *collections: list[str]) -> list[str]:
        merged: list[str] = []
        for collection in collections:
            merged.extend(collection or [])
        return unique_strings(merged)
