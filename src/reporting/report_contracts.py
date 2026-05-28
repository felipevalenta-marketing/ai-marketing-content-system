"""Structured report contracts for analytics and exports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.reporting.report_metrics import utc_now_iso


@dataclass(frozen=True)
class ReportContract:
    """Reusable structured report payload."""

    report_type: str
    title: str
    summary: dict[str, Any]
    metrics: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    metadata: dict[str, Any]
    sections: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report contract."""

        return {
            "report_type": self.report_type,
            "title": self.title,
            "summary": self.summary,
            "metrics": self.metrics,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
            "sections": self.sections,
            "generated_at": self.generated_at,
        }


def _build_report(
    report_type: str,
    title: str,
    summary: dict[str, Any],
    metrics: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    sections: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return ReportContract(
        report_type=report_type,
        title=title,
        summary=summary,
        metrics=metrics,
        warnings=warnings or [],
        errors=errors or [],
        metadata=metadata or {},
        sections=sections or {},
    ).to_dict()


def build_execution_report(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    sections: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an execution report."""

    return _build_report("execution", "Execution Report", summary, metrics, warnings, errors, metadata, sections)


def build_governance_report(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    sections: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a governance report."""

    return _build_report("governance", "Governance Report", summary, metrics, warnings, errors, metadata, sections)


def build_campaign_report(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    sections: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a campaign report."""

    return _build_report("campaign", "Campaign Report", summary, metrics, warnings, errors, metadata, sections)


def build_asset_report(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    sections: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an asset report."""

    return _build_report("asset", "Asset Report", summary, metrics, warnings, errors, metadata, sections)


def build_export_report(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    sections: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an export report."""

    return _build_report("export", "Export Report", summary, metrics, warnings, errors, metadata, sections)


def build_consolidated_report(
    summary: dict[str, Any],
    metrics: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    sections: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a consolidated report."""

    return _build_report("consolidated", "Consolidated Report", summary, metrics, warnings, errors, metadata, sections)
