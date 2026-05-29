"""Contracts for analytics requests, KPIs, and dashboard payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.reporting.report_metrics import utc_now_iso


SUPPORTED_ANALYTICS_TYPES = (
    "executive_dashboard",
    "workflow_analytics",
    "campaign_analytics",
    "generation_analytics",
    "asset_analytics",
    "token_analytics",
    "cost_analytics",
    "governance_analytics",
    "report_analytics",
    "storage_analytics",
    "api_health_analytics",
)


@dataclass(frozen=True)
class AnalyticsRequestContract:
    analytics_type: str
    brand: str = ""
    platform: str = ""
    date_range: dict[str, str] = field(default_factory=lambda: {"start": "", "end": ""})
    filters: dict[str, str] = field(default_factory=dict)
    include_storage: bool = True
    include_tokens: bool = True
    include_costs: bool = True
    include_governance: bool = True
    include_reports: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "analytics_type": self.analytics_type,
            "brand": self.brand,
            "platform": self.platform,
            "date_range": self.date_range,
            "filters": self.filters,
            "include_storage": self.include_storage,
            "include_tokens": self.include_tokens,
            "include_costs": self.include_costs,
            "include_governance": self.include_governance,
            "include_reports": self.include_reports,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class KPIContract:
    label: str
    value: Any
    unit: str = ""
    status: str = "neutral"
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "value": self.value,
            "unit": self.unit,
            "status": self.status,
            "description": self.description,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class TrendContract:
    name: str
    series: dict[str, int]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "series": self.series, "metadata": self.metadata}


@dataclass(frozen=True)
class InsightContract:
    text: str
    severity: str = "neutral"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "severity": self.severity, "metadata": self.metadata}


@dataclass(frozen=True)
class RecommendationContract:
    text: str
    priority: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"text": self.text, "priority": self.priority, "metadata": self.metadata}


@dataclass(frozen=True)
class DashboardPayloadContract:
    cards: list[dict[str, Any]] = field(default_factory=list)
    tables: dict[str, Any] = field(default_factory=dict)
    summaries: dict[str, Any] = field(default_factory=dict)
    recent_activity: list[dict[str, Any]] = field(default_factory=list)
    health: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cards": self.cards,
            "tables": self.tables,
            "summaries": self.summaries,
            "recent_activity": self.recent_activity,
            "health": self.health,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass(frozen=True)
class AnalyticsResultContract:
    success: bool
    analytics_type: str
    generated_at: str = field(default_factory=utc_now_iso)
    date_range: dict[str, str] = field(default_factory=lambda: {"start": "", "end": ""})
    filters: dict[str, Any] = field(default_factory=dict)
    executive_summary: dict[str, Any] = field(default_factory=dict)
    kpis: dict[str, Any] = field(default_factory=dict)
    sections: dict[str, Any] = field(default_factory=dict)
    trends: dict[str, Any] = field(default_factory=dict)
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "analytics_type": self.analytics_type,
            "generated_at": self.generated_at,
            "date_range": self.date_range,
            "filters": self.filters,
            "executive_summary": self.executive_summary,
            "kpis": self.kpis,
            "sections": self.sections,
            "trends": self.trends,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }

