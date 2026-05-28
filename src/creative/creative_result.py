"""Structured creative direction result helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CreativeDirectionResult:
    """Reusable creative direction result container."""

    success: bool
    creative_direction_type: str
    brand: str
    campaign_type: str
    visual_identity: dict[str, Any]
    moodboard: dict[str, Any]
    color_palette: dict[str, Any]
    lighting_direction: str
    camera_style: str
    composition_rules: list[dict[str, Any]]
    platform_guidelines: dict[str, Any]
    media_guidelines: dict[str, Any]
    asset_guidelines: dict[str, Any]
    governance_notes: list[str]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result."""

        return {
            "success": self.success,
            "creative_direction_type": self.creative_direction_type,
            "brand": self.brand,
            "campaign_type": self.campaign_type,
            "visual_identity": self.visual_identity,
            "moodboard": self.moodboard,
            "color_palette": self.color_palette,
            "lighting_direction": self.lighting_direction,
            "camera_style": self.camera_style,
            "composition_rules": self.composition_rules,
            "platform_guidelines": self.platform_guidelines,
            "media_guidelines": self.media_guidelines,
            "asset_guidelines": self.asset_guidelines,
            "governance_notes": self.governance_notes,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
            "validation": self.validation,
        }


def build_creative_direction_success(
    *,
    creative_direction_type: str,
    brand: str,
    campaign_type: str,
    visual_identity: dict[str, Any],
    moodboard: dict[str, Any],
    color_palette: dict[str, Any],
    lighting_direction: str,
    camera_style: str,
    composition_rules: list[dict[str, Any]],
    platform_guidelines: dict[str, Any],
    media_guidelines: dict[str, Any],
    asset_guidelines: dict[str, Any],
    governance_notes: list[str],
    metadata: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a successful creative direction response."""

    return CreativeDirectionResult(
        success=True,
        creative_direction_type=creative_direction_type,
        brand=brand,
        campaign_type=campaign_type,
        visual_identity=visual_identity,
        moodboard=moodboard,
        color_palette=color_palette,
        lighting_direction=lighting_direction,
        camera_style=camera_style,
        composition_rules=composition_rules,
        platform_guidelines=platform_guidelines,
        media_guidelines=media_guidelines,
        asset_guidelines=asset_guidelines,
        governance_notes=governance_notes,
        metadata=metadata,
        warnings=warnings or [],
        errors=errors or [],
        validation=validation or {},
    ).to_dict()


def build_creative_direction_failure(
    *,
    creative_direction_type: str,
    brand: str,
    campaign_type: str,
    metadata: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a failed creative direction response."""

    return CreativeDirectionResult(
        success=False,
        creative_direction_type=creative_direction_type,
        brand=brand,
        campaign_type=campaign_type,
        visual_identity={},
        moodboard={},
        color_palette={},
        lighting_direction="",
        camera_style="",
        composition_rules=[],
        platform_guidelines={},
        media_guidelines={},
        asset_guidelines={},
        governance_notes=[],
        metadata=metadata,
        warnings=warnings or [],
        errors=errors or [],
        validation=validation or {},
    ).to_dict()
