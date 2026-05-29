"""Central analytics orchestration for dashboard-ready insights."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.analytics.analytics_contracts import SUPPORTED_ANALYTICS_TYPES
from src.analytics.analytics_result import (
    build_dashboard_payload_result,
    build_empty_result,
    build_failure_result,
    build_success_result,
)
from src.analytics.dashboard_payload import DashboardPayloadBuilder
from src.analytics.executive_summary import ExecutiveSummary
from src.analytics.insight_generator import InsightGenerator
from src.analytics.kpi_builder import KPIBuilder
from src.analytics.metric_aggregator import MetricAggregator
from src.analytics.metric_collector import MetricCollector
from src.analytics.metric_validator import MetricValidator
from src.analytics.trend_analyzer import TrendAnalyzer
from src.reporting.report_metrics import safe_dict, safe_list, safe_text, utc_now_iso
from src.utils.logger import get_logger, log_context, log_warning


class AnalyticsEngine:
    def __init__(self, storage_manager: Any | None = None, reporting_engine: Any | None = None, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.storage_manager = storage_manager
        self.reporting_engine = reporting_engine
        self.collector = MetricCollector(storage_manager=storage_manager, logger=self.logger)
        self.aggregator = MetricAggregator()
        self.kpi_builder = KPIBuilder()
        self.summary_builder = ExecutiveSummary()
        self.trend_analyzer = TrendAnalyzer()
        self.insight_generator = InsightGenerator()
        self.dashboard_builder = DashboardPayloadBuilder()
        self.validator = MetricValidator()

    def generate_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        analytics_type = safe_text(request.get("analytics_type") or "executive_dashboard", limit=80)
        if analytics_type not in SUPPORTED_ANALYTICS_TYPES:
            return build_failure_result(f"Unsupported analytics_type: {analytics_type}", analytics_type=analytics_type, date_range=safe_dict(request.get("date_range")), filters=safe_dict(request.get("filters")))

        if analytics_type == "executive_dashboard":
            return self.generate_executive_dashboard(request)
        if analytics_type == "workflow_analytics":
            return self.generate_workflow_analytics(request)
        if analytics_type == "campaign_analytics":
            return self.generate_campaign_analytics(request)
        if analytics_type == "generation_analytics":
            return self.generate_generation_analytics(request)
        if analytics_type == "asset_analytics":
            return self.generate_asset_analytics(request)
        if analytics_type == "token_analytics":
            return self.generate_token_analytics(request)
        if analytics_type == "cost_analytics":
            return self.generate_cost_analytics(request)
        if analytics_type == "governance_analytics":
            return self.generate_governance_analytics(request)
        if analytics_type == "report_analytics":
            return self.generate_report_analytics(request)
        if analytics_type == "storage_analytics":
            return self.generate_storage_analytics(request)
        if analytics_type == "api_health_analytics":
            return self._generate_api_health_analytics(request)
        return self.generate_executive_dashboard(request)

    def generate_executive_dashboard(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_dashboard_context(request)
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "executive_dashboard"
        analytics["sections"] = self._build_dashboard_sections(collected, request)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        if not self._has_data(collected):
            analytics["metadata"] = self._metadata(request, collected)
            return build_empty_result(**analytics)
        analytics["metadata"] = self._metadata(request, collected)
        return build_success_result(**analytics)

    def generate_workflow_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, include_storage=True, include_tokens=bool(request.get("include_tokens", True)), include_costs=bool(request.get("include_costs", True)), record_types=["workflow", "report", "token_usage", "cost_usage"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "workflow_analytics"
        analytics["sections"] = self._workflow_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def generate_campaign_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, include_storage=bool(request.get("include_storage", True)), record_types=["campaign", "report"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "campaign_analytics"
        analytics["sections"] = self._campaign_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def generate_generation_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, record_types=["generation", "report", "token_usage", "cost_usage"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "generation_analytics"
        analytics["sections"] = self._generation_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def generate_asset_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, record_types=["asset", "image_prompt", "video_script", "creative_direction", "report"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "asset_analytics"
        analytics["sections"] = self._asset_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def generate_token_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, record_types=["token_usage"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "token_analytics"
        analytics["sections"] = self._token_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def generate_cost_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, record_types=["cost_usage"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "cost_analytics"
        analytics["sections"] = self._cost_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def generate_governance_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, record_types=["workflow", "report"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "governance_analytics"
        analytics["sections"] = self._governance_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def generate_report_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, record_types=["report"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "report_analytics"
        analytics["sections"] = self._report_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def generate_storage_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, include_storage=True, record_types=None)
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "storage_analytics"
        analytics["sections"] = self._storage_sections(collected)
        analytics["kpis"] = self.kpi_builder.build_kpis(analytics)
        analytics["executive_summary"] = self.summary_builder.build_executive_summary(analytics)
        analytics["trends"] = self._build_trends(collected)
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def build_dashboard_payload(self, request: dict[str, Any]) -> dict[str, Any]:
        result = self.generate_executive_dashboard(request)
        payload = safe_dict(result.get("dashboard_payload"))
        return build_dashboard_payload_result(
            analytics_type=safe_text(result.get("analytics_type"), limit=80),
            date_range=safe_dict(result.get("date_range")),
            filters=safe_dict(result.get("filters")),
            dashboard_payload=payload,
            executive_summary=safe_dict(result.get("executive_summary")),
            kpis=safe_dict(result.get("kpis")),
            sections=safe_dict(result.get("sections")),
            trends=safe_dict(result.get("trends")),
            insights=safe_list(result.get("insights")),
            recommendations=safe_list(result.get("recommendations")),
            warnings=safe_list(result.get("warnings")),
            errors=safe_list(result.get("errors")),
            metadata=safe_dict(result.get("metadata")),
        )

    def build_result(self, **kwargs: Any) -> dict[str, Any]:
        return build_success_result(**kwargs)

    def _generate_api_health_analytics(self, request: dict[str, Any]) -> dict[str, Any]:
        collected = self._collect_context(request, record_types=["report"])
        analytics = self._build_analytics_base(request, collected)
        analytics["analytics_type"] = "api_health_analytics"
        health = {
            "status": "healthy" if self.storage_manager is not None else "degraded",
            "storage_available": self.storage_manager is not None,
            "data_available": self._has_data(collected),
            "warnings_count": len(safe_list(self.collector.warnings)),
            "errors_count": 0,
        }
        analytics["sections"] = {"health": health}
        analytics["kpis"] = {"executive": {}, "operational": {}}
        analytics["executive_summary"] = {
            "headline": "API health summary",
            "outcome": "Analytics subsystem is available." if self.storage_manager is not None else "Storage is unavailable.",
            "approval_status": "approved" if self.storage_manager is not None else "review",
            "generated_assets": 0,
            "workflow_status": "",
            "token_summary": "",
            "cost_summary": "",
            "governance_summary": "",
            "key_warnings": safe_list(self.collector.warnings),
            "critical_errors": [],
            "next_actions": ["Verify storage connectivity and persisted records."],
            "report_type": "api_health_analytics",
            "activity_status": "healthy" if self.storage_manager is not None else "degraded",
        }
        analytics["trends"] = {}
        analytics["insights"] = self.insight_generator.generate_insights(analytics)
        analytics["recommendations"] = self.insight_generator.generate_recommendations(analytics)
        analytics["dashboard_payload"] = self.dashboard_builder.build_dashboard_payload(analytics)
        analytics["validation"] = self.validator.validate(analytics)
        analytics.update(analytics["validation"])
        return self._wrap_result(analytics, collected, request)

    def _build_analytics_base(self, request: dict[str, Any], collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        analytics_type = safe_text(request.get("analytics_type") or "executive_dashboard", limit=80)
        date_range = safe_dict(request.get("date_range")) or {"start": "", "end": ""}
        filters = safe_dict(request.get("filters"))
        analytics = {
            "analytics_type": analytics_type,
            "generated_at": utc_now_iso(),
            "date_range": {"start": safe_text(date_range.get("start"), limit=80), "end": safe_text(date_range.get("end"), limit=80)},
            "filters": filters,
            "warnings": [],
            "errors": [],
            "metadata": self._metadata(request, collected),
        }
        return analytics

    def _collect_dashboard_context(self, request: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        collected = self._collect_context(
            request,
            include_storage=bool(request.get("include_storage", True)),
            include_tokens=bool(request.get("include_tokens", True)),
            include_costs=bool(request.get("include_costs", True)),
            include_governance=bool(request.get("include_governance", True)),
            include_reports=bool(request.get("include_reports", True)),
            record_types=["workflow", "generation", "campaign", "asset", "report", "token_usage", "cost_usage", "creative_direction", "image_prompt", "video_script"],
        )
        return collected

    def _collect_context(self, request: dict[str, Any], include_storage: bool = True, include_tokens: bool = True, include_costs: bool = True, include_governance: bool = True, include_reports: bool = True, record_types: list[str] | None = None) -> dict[str, list[dict[str, Any]]]:
        self.collector.clear_warnings()
        filters = safe_dict(request.get("filters"))
        base_filters = {key: value for key, value in filters.items() if value not in (None, "", [], {})}
        if request.get("brand"):
            base_filters["brand"] = request.get("brand")
        if request.get("platform"):
            base_filters["platform"] = request.get("platform")
        if request.get("organization_id"):
            base_filters["organization_id"] = request.get("organization_id")
        if request.get("team_id"):
            base_filters["team_id"] = request.get("team_id")
        base_filters["date_range"] = safe_dict(request.get("date_range"))
        collected: dict[str, list[dict[str, Any]]] = {}
        if not include_storage:
            return collected
        record_map: dict[str, list[dict[str, Any]]] = {
            "execution": self.collector.collect_records("execution", base_filters),
            "workflow": self.collector.collect_workflow_records(base_filters),
            "workflow_state": self.collector.collect_records("workflow_state", base_filters),
            "generation": self.collector.collect_generation_records(base_filters),
            "campaign": self.collector.collect_campaign_records(base_filters),
            "asset": self.collector.collect_asset_records(base_filters),
            "report": self.collector.collect_report_records(base_filters) if include_reports else [],
            "token_usage": self.collector.collect_token_records(base_filters) if include_tokens else [],
            "cost_usage": self.collector.collect_cost_records(base_filters) if include_costs else [],
            "governance": self.collector.collect_governance_records(base_filters) if include_governance else [],
            "creative_direction": self.collector.collect_records("creative_direction", base_filters),
            "image_prompt": self.collector.collect_records("image_prompt", base_filters),
            "video_script": self.collector.collect_records("video_script", base_filters),
            "snapshot": self.collector.collect_records("snapshot", base_filters),
        }
        if record_types:
            return {key: value for key, value in record_map.items() if key in set(record_types) or key in {"report", "token_usage", "cost_usage", "governance"}}
        return record_map

    def _build_dashboard_sections(self, collected: dict[str, list[dict[str, Any]]], request: dict[str, Any]) -> dict[str, Any]:
        workflow_records = collected.get("workflow", [])
        generation_records = collected.get("generation", [])
        campaign_records = collected.get("campaign", [])
        asset_records = collected.get("asset", [])
        report_records = collected.get("report", [])
        token_records = collected.get("token_usage", [])
        cost_records = collected.get("cost_usage", [])
        governance_records = collected.get("governance", [])
        storage_records = self._flatten_records(collected)
        latest_execution_at = self._latest_timestamp(workflow_records + generation_records + campaign_records + asset_records)
        latest_report_at = self._latest_timestamp(report_records)
        report_summary = self._latest_record(report_records)
        return {
            "workflows": self.aggregator.aggregate_workflows(workflow_records),
            "generations": self.aggregator.aggregate_counts(generation_records),
            "campaigns": self.aggregator.aggregate_counts(campaign_records),
            "assets": self.aggregator.aggregate_counts(asset_records),
            "reports": self.aggregator.aggregate_counts(report_records),
            "tokens": self.aggregator.aggregate_tokens(token_records),
            "costs": self.aggregator.aggregate_costs(cost_records),
            "governance": self.aggregator.aggregate_governance(governance_records),
            "storage": {"records_count": len(storage_records), "latest_execution_at": latest_execution_at, "latest_report_at": latest_report_at},
            "brand_breakdown": self.aggregator.aggregate_by_brand(storage_records),
            "organization_breakdown": self.aggregator.aggregate_by_organization(storage_records),
            "team_breakdown": self.aggregator.aggregate_by_team(storage_records),
            "platform_breakdown": self.aggregator.aggregate_by_platform(storage_records),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(storage_records),
            "report_summary": report_summary,
            "workflow_snapshot": self._latest_workflow_snapshot(workflow_records),
            "workflow_state_history": self._latest_state_history(workflow_records),
            "workflow_timeline": self._latest_timeline(workflow_records),
            "workflow_status_transitions": self._latest_status_transitions(workflow_records),
            "analytics_type": "executive_dashboard",
            "filters": safe_dict(request.get("filters")),
            "date_range": safe_dict(request.get("date_range")),
            "organization_breakdown": self.aggregator.aggregate_by_organization(storage_records),
            "team_breakdown": self.aggregator.aggregate_by_team(storage_records),
        }

    def _workflow_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        workflows = collected.get("workflow", [])
        return {
            "workflows": self.aggregator.aggregate_workflows(workflows),
            "tokens": self.aggregator.aggregate_tokens(collected.get("token_usage", [])),
            "costs": self.aggregator.aggregate_costs(collected.get("cost_usage", [])),
            "storage": {"records_count": len(self._flatten_records(collected))},
            "report_summary": self._latest_record(collected.get("report", [])),
            "workflow_snapshot": self._latest_workflow_snapshot(workflows),
            "workflow_state_history": self._latest_state_history(workflows),
            "workflow_timeline": self._latest_timeline(workflows),
            "workflow_status_transitions": self._latest_status_transitions(workflows),
        }

    def _campaign_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        campaigns = collected.get("campaign", [])
        assets = collected.get("asset", [])
        return {
            "campaigns": self.aggregator.aggregate_counts(campaigns),
            "assets": self.aggregator.aggregate_counts(assets),
            "tokens": self.aggregator.aggregate_tokens(collected.get("token_usage", [])),
            "costs": self.aggregator.aggregate_costs(collected.get("cost_usage", [])),
            "storage": {"records_count": len(self._flatten_records(collected))},
            "brand_breakdown": self.aggregator.aggregate_by_brand(campaigns),
            "organization_breakdown": self.aggregator.aggregate_by_organization(campaigns),
            "team_breakdown": self.aggregator.aggregate_by_team(campaigns),
            "platform_breakdown": self.aggregator.aggregate_by_platform(campaigns),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(campaigns),
        }

    def _generation_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        generations = collected.get("generation", [])
        return {
            "generations": self.aggregator.aggregate_counts(generations),
            "tokens": self.aggregator.aggregate_tokens(collected.get("token_usage", [])),
            "costs": self.aggregator.aggregate_costs(collected.get("cost_usage", [])),
            "storage": {"records_count": len(self._flatten_records(collected))},
            "brand_breakdown": self.aggregator.aggregate_by_brand(generations),
            "organization_breakdown": self.aggregator.aggregate_by_organization(generations),
            "team_breakdown": self.aggregator.aggregate_by_team(generations),
            "platform_breakdown": self.aggregator.aggregate_by_platform(generations),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(generations),
        }

    def _asset_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        assets = collected.get("asset", [])
        creative = collected.get("creative_direction", [])
        image_prompts = collected.get("image_prompt", [])
        video_scripts = collected.get("video_script", [])
        return {
            "assets": self.aggregator.aggregate_counts(assets),
            "creative_direction": self.aggregator.aggregate_counts(creative),
            "image_prompts": self.aggregator.aggregate_counts(image_prompts),
            "video_scripts": self.aggregator.aggregate_counts(video_scripts),
            "tokens": self.aggregator.aggregate_tokens(collected.get("token_usage", [])),
            "costs": self.aggregator.aggregate_costs(collected.get("cost_usage", [])),
            "storage": {"records_count": len(self._flatten_records(collected))},
            "brand_breakdown": self.aggregator.aggregate_by_brand(assets),
            "organization_breakdown": self.aggregator.aggregate_by_organization(assets),
            "team_breakdown": self.aggregator.aggregate_by_team(assets),
            "platform_breakdown": self.aggregator.aggregate_by_platform(assets),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(assets),
        }

    def _token_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        tokens = collected.get("token_usage", [])
        return {
            "tokens": self.aggregator.aggregate_tokens(tokens),
            "storage": {"records_count": len(self._flatten_records(collected))},
            "brand_breakdown": self.aggregator.aggregate_by_brand(tokens),
            "organization_breakdown": self.aggregator.aggregate_by_organization(tokens),
            "team_breakdown": self.aggregator.aggregate_by_team(tokens),
            "platform_breakdown": self.aggregator.aggregate_by_platform(tokens),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(tokens),
        }

    def _cost_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        costs = collected.get("cost_usage", [])
        return {
            "costs": self.aggregator.aggregate_costs(costs),
            "storage": {"records_count": len(self._flatten_records(collected))},
            "brand_breakdown": self.aggregator.aggregate_by_brand(costs),
            "organization_breakdown": self.aggregator.aggregate_by_organization(costs),
            "team_breakdown": self.aggregator.aggregate_by_team(costs),
            "platform_breakdown": self.aggregator.aggregate_by_platform(costs),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(costs),
        }

    def _governance_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        governance = collected.get("governance", [])
        return {
            "governance": self.aggregator.aggregate_governance(governance),
            "storage": {"records_count": len(self._flatten_records(collected))},
            "brand_breakdown": self.aggregator.aggregate_by_brand(governance),
            "organization_breakdown": self.aggregator.aggregate_by_organization(governance),
            "team_breakdown": self.aggregator.aggregate_by_team(governance),
            "platform_breakdown": self.aggregator.aggregate_by_platform(governance),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(governance),
        }

    def _report_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        reports = collected.get("report", [])
        return {
            "reports": self.aggregator.aggregate_counts(reports),
            "storage": {"records_count": len(self._flatten_records(collected))},
            "brand_breakdown": self.aggregator.aggregate_by_brand(reports),
            "organization_breakdown": self.aggregator.aggregate_by_organization(reports),
            "team_breakdown": self.aggregator.aggregate_by_team(reports),
            "platform_breakdown": self.aggregator.aggregate_by_platform(reports),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(reports),
        }

    def _storage_sections(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        records = self._flatten_records(collected)
        return {
            "storage": {"records_count": len(records), "latest_execution_at": self._latest_timestamp(records), "latest_report_at": self._latest_timestamp(collected.get("report", []))},
            "brand_breakdown": self.aggregator.aggregate_by_brand(records),
            "organization_breakdown": self.aggregator.aggregate_by_organization(records),
            "team_breakdown": self.aggregator.aggregate_by_team(records),
            "platform_breakdown": self.aggregator.aggregate_by_platform(records),
            "content_type_breakdown": self.aggregator.aggregate_by_content_type(records),
        }

    def _build_trends(self, collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        records = self._flatten_records(collected)
        return {
            "by_day": self.trend_analyzer.group_by_day(records),
            "by_brand": self.trend_analyzer.group_by_brand(records),
            "by_platform": self.trend_analyzer.group_by_platform(records),
            "recent_activity": self.trend_analyzer.summarize_recent_activity(records, limit=10),
        }

    def _latest_record(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        if not records:
            return {}
        ordered = self.trend_analyzer.summarize_recent_activity(records, limit=1)
        if not ordered:
            return {}
        record_id = safe_text(ordered[0].get("record_id"), limit=120)
        for record in records:
            if safe_text(record.get("record_id"), limit=120) == record_id:
                return deepcopy(record)
        return deepcopy(records[0])

    def _latest_workflow_snapshot(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        latest = self._latest_record(records)
        payload = safe_dict(latest.get("payload"))
        return safe_dict(
            latest.get("workflow_snapshot")
            or latest.get("workflow_state")
            or payload.get("workflow_snapshot")
            or payload.get("workflow_state")
            or safe_dict(payload.get("state"))
        )

    def _latest_state_history(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        latest = self._latest_record(records)
        payload = safe_dict(latest.get("payload"))
        return safe_list(
            latest.get("workflow_state_history")
            or safe_dict(latest.get("workflow_state")).get("history")
            or payload.get("workflow_state_history")
            or safe_dict(payload.get("workflow_state")).get("history")
        )

    def _latest_timeline(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        latest = self._latest_record(records)
        payload = safe_dict(latest.get("payload"))
        return safe_list(
            latest.get("workflow_timeline")
            or safe_dict(latest.get("workflow_state")).get("timeline")
            or payload.get("workflow_timeline")
            or safe_dict(payload.get("workflow_state")).get("timeline")
        )

    def _latest_status_transitions(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        latest = self._latest_record(records)
        payload = safe_dict(latest.get("payload"))
        return safe_list(
            latest.get("workflow_status_transitions")
            or safe_dict(latest.get("workflow_state")).get("status_transitions")
            or payload.get("workflow_status_transitions")
            or safe_dict(payload.get("workflow_state")).get("status_transitions")
        )

    def _latest_timestamp(self, records: list[dict[str, Any]]) -> str:
        latest = self._latest_record(records)
        return safe_text(latest.get("created_at") or latest.get("updated_at") or "", limit=80)

    def _flatten_records(self, collected: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        flattened: list[dict[str, Any]] = []
        for record_list in collected.values():
            flattened.extend([record for record in safe_list(record_list) if isinstance(record, dict)])
        return flattened

    def _metadata(self, request: dict[str, Any], collected: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
        return {
            "brand": safe_text(request.get("brand"), limit=80),
            "platform": safe_text(request.get("platform"), limit=80),
            "analytics_type": safe_text(request.get("analytics_type"), limit=80),
            "records_collected": sum(len(value) for value in collected.values()),
            "storage_available": self.storage_manager is not None,
            "warnings": list(self.collector.warnings),
        }

    def _has_data(self, collected: dict[str, list[dict[str, Any]]]) -> bool:
        return any(collected.values())

    def _wrap_result(self, analytics: dict[str, Any], collected: dict[str, list[dict[str, Any]]], request: dict[str, Any]) -> dict[str, Any]:
        analytics.setdefault("warnings", [])
        analytics.setdefault("errors", [])
        analytics["warnings"] = list(dict.fromkeys([safe_text(item, limit=240) for item in safe_list(analytics.get("warnings")) if safe_text(item, limit=240)] + [safe_text(item, limit=240) for item in self.collector.warnings if safe_text(item, limit=240)]))
        analytics["errors"] = list(dict.fromkeys([safe_text(item, limit=240) for item in safe_list(analytics.get("errors")) if safe_text(item, limit=240)]))
        analytics["metadata"] = {**safe_dict(analytics.get("metadata")), **self._metadata(request, collected)}
        if analytics.get("analytics_type") == "api_health_analytics":
            return build_success_result(**analytics)
        if not self._has_data(collected):
            return build_empty_result(**analytics)
        return build_success_result(**analytics)

if __name__ == "__main__":
    engine = AnalyticsEngine()
    print("Executive dashboard:", engine.generate_executive_dashboard({"analytics_type": "executive_dashboard"}))
    print("Empty storage:", engine.generate_storage_analytics({"analytics_type": "storage_analytics"}))
    print("Token analytics:", engine.generate_token_analytics({"analytics_type": "token_analytics"}))
    print("Cost analytics:", engine.generate_cost_analytics({"analytics_type": "cost_analytics"}))
    print("Workflow analytics:", engine.generate_workflow_analytics({"analytics_type": "workflow_analytics"}))
    print("Governance analytics:", engine.generate_governance_analytics({"analytics_type": "governance_analytics"}))
    print("Dashboard payload:", engine.build_dashboard_payload({"analytics_type": "executive_dashboard"}))
