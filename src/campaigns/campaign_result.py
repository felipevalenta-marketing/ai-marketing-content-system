"""Structured result helpers for campaign composition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CampaignResult:
    """Container for a composed campaign pack."""

    success: bool
    campaign_name: str
    campaign_type: str
    objective: str
    brand: str
    audience: str
    location: str
    strategy: dict[str, Any]
    asset_plan: dict[str, Any]
    assets: dict[str, Any]
    platform_plan: dict[str, Any]
    content_sequence: list[dict[str, Any]]
    governance_summary: dict[str, Any]
    metadata: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    export_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the campaign result."""

        return {
            "success": self.success,
            "campaign_name": self.campaign_name,
            "campaign_type": self.campaign_type,
            "objective": self.objective,
            "brand": self.brand,
            "audience": self.audience,
            "location": self.location,
            "strategy": self.strategy,
            "asset_plan": self.asset_plan,
            "assets": self.assets,
            "platform_plan": self.platform_plan,
            "content_sequence": self.content_sequence,
            "governance_summary": self.governance_summary,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
            "export_paths": self.export_paths,
        }


def build_campaign_success(
    campaign_name: str,
    campaign_type: str,
    objective: str,
    brand: str,
    audience: str,
    location: str,
    strategy: dict[str, Any],
    asset_plan: dict[str, Any],
    assets: dict[str, Any],
    platform_plan: dict[str, Any],
    content_sequence: list[dict[str, Any]],
    governance_summary: dict[str, Any],
    metadata: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    export_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a successful campaign result."""

    return CampaignResult(
        success=True,
        campaign_name=campaign_name,
        campaign_type=campaign_type,
        objective=objective,
        brand=brand,
        audience=audience,
        location=location,
        strategy=strategy,
        asset_plan=asset_plan,
        assets=assets,
        platform_plan=platform_plan,
        content_sequence=content_sequence,
        governance_summary=governance_summary,
        metadata=metadata,
        warnings=warnings or [],
        errors=errors or [],
        export_paths=export_paths or {},
    ).to_dict()


def build_campaign_failure(
    campaign_name: str,
    campaign_type: str,
    objective: str,
    brand: str,
    audience: str,
    location: str,
    strategy: dict[str, Any],
    asset_plan: dict[str, Any],
    platform_plan: dict[str, Any],
    content_sequence: list[dict[str, Any]],
    governance_summary: dict[str, Any],
    metadata: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    export_paths: dict[str, str] | None = None,
    assets: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a failed campaign result."""

    return CampaignResult(
        success=False,
        campaign_name=campaign_name,
        campaign_type=campaign_type,
        objective=objective,
        brand=brand,
        audience=audience,
        location=location,
        strategy=strategy,
        asset_plan=asset_plan,
        assets=assets or {},
        platform_plan=platform_plan,
        content_sequence=content_sequence,
        governance_summary=governance_summary,
        metadata=metadata,
        warnings=warnings or [],
        errors=errors or [],
        export_paths=export_paths or {},
    ).to_dict()
