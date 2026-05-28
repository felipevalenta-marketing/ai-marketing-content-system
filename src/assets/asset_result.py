"""Structured result helpers for asset coordination."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AssetResult:
    """Container for asset coordination output."""

    success: bool
    brand: str
    campaign_type: str
    objective: str
    asset_plan: dict[str, Any]
    asset_requirements: dict[str, Any]
    assets: dict[str, Any]
    planned_assets: list[str]
    existing_assets: list[str]
    missing_assets: list[str]
    invalid_assets: list[str]
    validation_result: dict[str, Any]
    metadata: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    export_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the asset coordination result."""

        return {
            "success": self.success,
            "brand": self.brand,
            "campaign_type": self.campaign_type,
            "objective": self.objective,
            "asset_plan": self.asset_plan,
            "asset_requirements": self.asset_requirements,
            "assets": self.assets,
            "planned_assets": self.planned_assets,
            "existing_assets": self.existing_assets,
            "missing_assets": self.missing_assets,
            "invalid_assets": self.invalid_assets,
            "validation_result": self.validation_result,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
            "export_paths": self.export_paths,
        }


def build_asset_success(
    brand: str,
    campaign_type: str,
    objective: str,
    asset_plan: dict[str, Any],
    asset_requirements: dict[str, Any],
    assets: dict[str, Any],
    planned_assets: list[str],
    existing_assets: list[str],
    missing_assets: list[str],
    invalid_assets: list[str],
    validation_result: dict[str, Any],
    metadata: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    export_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a success asset coordination payload."""

    return AssetResult(
        success=True,
        brand=brand,
        campaign_type=campaign_type,
        objective=objective,
        asset_plan=asset_plan,
        asset_requirements=asset_requirements,
        assets=assets,
        planned_assets=planned_assets,
        existing_assets=existing_assets,
        missing_assets=missing_assets,
        invalid_assets=invalid_assets,
        validation_result=validation_result,
        metadata=metadata,
        warnings=warnings or [],
        errors=errors or [],
        export_paths=export_paths or {},
    ).to_dict()


def build_asset_failure(
    brand: str,
    campaign_type: str,
    objective: str,
    asset_plan: dict[str, Any],
    asset_requirements: dict[str, Any],
    assets: dict[str, Any],
    planned_assets: list[str],
    existing_assets: list[str],
    missing_assets: list[str],
    invalid_assets: list[str],
    validation_result: dict[str, Any],
    metadata: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    export_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a failure asset coordination payload."""

    return AssetResult(
        success=False,
        brand=brand,
        campaign_type=campaign_type,
        objective=objective,
        asset_plan=asset_plan,
        asset_requirements=asset_requirements,
        assets=assets,
        planned_assets=planned_assets,
        existing_assets=existing_assets,
        missing_assets=missing_assets,
        invalid_assets=invalid_assets,
        validation_result=validation_result,
        metadata=metadata,
        warnings=warnings or [],
        errors=errors or [],
        export_paths=export_paths or {},
    ).to_dict()
