"""Asset planning structures for coordinated creative production."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.assets.asset_contracts import list_supported_asset_types, normalize_asset_type
from src.assets.asset_requirements import get_platform_requirements
from src.utils.file_utils import normalize_key


@dataclass(frozen=True)
class AssetPlan:
    """Describe the planned asset bundle for a request."""

    required_assets: list[str]
    optional_assets: list[str]
    platform_mapping: dict[str, list[str]]
    priority: dict[str, int]
    dependencies: dict[str, list[str]]
    status: str
    generation_readiness: dict[str, Any]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the plan."""

        return {
            "required_assets": self.required_assets,
            "optional_assets": self.optional_assets,
            "platform_mapping": self.platform_mapping,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status,
            "generation_readiness": self.generation_readiness,
            "notes": self.notes,
        }


def build_asset_plan(request: dict[str, Any]) -> dict[str, Any]:
    """Build a deterministic asset plan from a request."""

    requested_assets = [normalize_asset_type(asset) for asset in request.get("assets_required", []) if str(asset).strip()]
    platforms = [normalize_key(platform) for platform in request.get("platforms", []) if str(platform).strip()]
    if not requested_assets:
        requested_assets = ["social_post", "image_prompt", "video_prompt"]

    platform_mapping = {
        platform: [asset for asset in requested_assets if asset in get_platform_requirements(platform).get("asset_types", []) or asset in list_supported_asset_types()]
        for platform in platforms
    }

    optional_assets = [asset for asset in list_supported_asset_types() if asset not in requested_assets][:5]
    priority = {asset: index + 1 for index, asset in enumerate(requested_assets)}
    dependencies = _build_dependencies(requested_assets)
    readiness = {
        "ready": bool(requested_assets),
        "requested_asset_count": len(requested_assets),
        "supported_asset_count": len([asset for asset in requested_assets if asset in list_supported_asset_types()]),
        "image_prompt_ready": _build_image_prompt_readiness(request),
    }
    status = "planned" if requested_assets else "needs_review"
    notes = ["Asset plan is deterministic and derived from request inputs only."]
    if not platforms:
        notes.append("No target platforms were provided; plan is asset-centric.")
    return AssetPlan(
        required_assets=requested_assets,
        optional_assets=optional_assets,
        platform_mapping=platform_mapping,
        priority=priority,
        dependencies=dependencies,
        status=status,
        generation_readiness=readiness,
        notes=notes,
    ).to_dict()


def _build_image_prompt_readiness(request: dict[str, Any]) -> dict[str, Any]:
    """Summarize readiness for image prompt assets."""

    image_type = str(request.get("image_type", "")).strip()
    visual_style = str(request.get("visual_style", "")).strip()
    aspect_ratio = str(request.get("aspect_ratio", "")).strip()
    creative_direction = str(request.get("creative_direction", "")).strip()
    return {
        "ready": bool(image_type or visual_style or aspect_ratio or creative_direction),
        "image_type": image_type,
        "visual_style": visual_style,
        "aspect_ratio": aspect_ratio,
        "creative_direction": creative_direction,
    }


def _build_dependencies(requested_assets: list[str]) -> dict[str, list[str]]:
    """Build lightweight deterministic dependencies."""

    dependencies: dict[str, list[str]] = {}
    for asset in requested_assets:
        if asset in {"image_prompt", "video_prompt"}:
            dependencies[asset] = ["campaign_strategy", "creative_direction"]
        elif asset in {"email_teaser", "website_listing", "campaign_summary", "campaign_bundle"}:
            dependencies[asset] = ["formatted_output", "governance_summary"]
        elif asset in {"social_post", "text_caption", "reel_script"}:
            dependencies[asset] = ["formatted_output", "platform_rules"]
        else:
            dependencies[asset] = []
    return dependencies
