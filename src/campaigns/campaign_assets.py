"""Campaign asset normalization and packaging helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


ASSET_STATUSES = ("approved", "warning", "rejected", "missing")


@dataclass(frozen=True)
class CampaignAsset:
    """Normalized campaign asset representation."""

    asset_type: str
    platform: str
    purpose: str
    content: dict[str, Any]
    formatted_output: dict[str, Any]
    platform_variant: dict[str, Any]
    governance_result: dict[str, Any]
    metadata: dict[str, Any]
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the campaign asset."""

        return {
            "asset_type": self.asset_type,
            "platform": self.platform,
            "purpose": self.purpose,
            "content": self.content,
            "formatted_output": self.formatted_output,
            "platform_variant": self.platform_variant,
            "governance_result": self.governance_result,
            "metadata": self.metadata,
            "status": self.status,
        }


def normalize_campaign_assets(assets: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Normalize a mixed asset payload into campaign asset objects."""

    normalized: dict[str, dict[str, Any]] = {}
    for asset_key, asset_value in (assets or {}).items():
        normalized_key = normalize_key(asset_key)
        normalized[normalized_key] = _normalize_asset(normalized_key, asset_value)
    return normalized


def _normalize_asset(asset_type: str, asset_value: Any) -> dict[str, Any]:
    if isinstance(asset_value, CampaignAsset):
        return asset_value.to_dict()

    if isinstance(asset_value, dict):
        content = asset_value.get("content")
        if not isinstance(content, dict):
            content = {}
        formatted_output = asset_value.get("formatted_output")
        if not isinstance(formatted_output, dict):
            formatted_output = content
        platform_variant = asset_value.get("platform_variant")
        if not isinstance(platform_variant, dict):
            platform_variant = {}
        governance_result = asset_value.get("governance_result")
        if not isinstance(governance_result, dict):
            governance_result = {}
        metadata = asset_value.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}
        status = _derive_status(asset_value)
        return CampaignAsset(
            asset_type=normalize_key(str(asset_value.get("asset_type", asset_type))),
            platform=normalize_key(str(asset_value.get("platform", ""))),
            purpose=str(asset_value.get("purpose", "")).strip(),
            content=content,
            formatted_output=formatted_output,
            platform_variant=platform_variant,
            governance_result=governance_result,
            metadata=metadata,
            status=status,
        ).to_dict()

    return CampaignAsset(
        asset_type=asset_type,
        platform="",
        purpose="",
        content={},
        formatted_output={},
        platform_variant={},
        governance_result={},
        metadata={},
        status="missing",
    ).to_dict()


def _derive_status(asset_value: dict[str, Any]) -> str:
    status = str(asset_value.get("status", "")).strip().lower()
    if status in ASSET_STATUSES:
        return status
    governance_result = asset_value.get("governance_result")
    if isinstance(governance_result, dict):
        if governance_result.get("approved") is True:
            return "approved" if str(governance_result.get("status", "")).startswith("approved") else "warning"
        if governance_result.get("status") == "rejected":
            return "rejected"
    if asset_value.get("formatted_output"):
        return "warning"
    return "missing"
