"""Configuration settings for the end-to-end generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_SUPPORTED_CONTENT_TYPES = (
    "instagram_post",
    "instagram_reel",
    "property_description",
    "image_prompt",
    "video_prompt",
    "campaign_asset",
)

DEFAULT_SUPPORTED_PLATFORMS = (
    "instagram",
    "facebook",
    "linkedin",
    "seo",
    "image",
    "video",
    "email",
    "web",
)


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration for the generation pipeline."""

    brands_root: str = "brands"
    default_brand: str = "wenzel_partner"
    default_platform: str = "instagram"
    default_content_type: str = "instagram_post"
    enable_live_generation: bool = True
    enable_output_formatting: bool = True
    enable_output_validation: bool = True
    enable_rendering: bool = True
    enable_export: bool = False
    enable_platform_adaptation: bool = False
    enable_governance_validation: bool = False
    enable_campaign_composition: bool = False
    enable_campaign_export: bool = False
    enable_asset_coordination: bool = False
    enable_asset_export: bool = False
    enable_reporting: bool = False
    enable_report_export: bool = False
    governance_min_score: float = 70.0
    reject_on_critical_safety_error: bool = True
    supported_platforms: tuple[str, ...] = DEFAULT_SUPPORTED_PLATFORMS
    supported_content_types: tuple[str, ...] = DEFAULT_SUPPORTED_CONTENT_TYPES
    target_platforms: list[str] = field(default_factory=lambda: ["instagram"])
    default_target_platforms: list[str] = field(default_factory=lambda: ["instagram", "facebook", "linkedin"])
    default_asset_types: list[str] = field(default_factory=lambda: ["text_caption", "image_prompt", "video_prompt"])
    asset_output_root: str = "outputs"
    export_formats: tuple[str, ...] = ("markdown", "json")
    output_root: str = "outputs"
    campaign_output_root: str = "outputs"
    report_output_root: str = "outputs/reports"
    report_formats: tuple[str, ...] = ("markdown", "json")
    default_campaign_type: str = "property_launch"
    generation_defaults: dict[str, Any] = field(
        default_factory=lambda: {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_output_tokens": 1200,
            "timeout_seconds": 60,
        }
    )
    validation_rules: dict[str, Any] = field(
        default_factory=lambda: {
            "required_fields": ("brand", "platform", "content_type", "objective", "audience"),
            "allow_extra_notes": True,
        }
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def supports_platform(self, platform: str) -> bool:
        """Return whether a platform is supported by the pipeline."""

        return str(platform).strip().lower() in self.supported_platforms

    def supports_content_type(self, content_type: str) -> bool:
        """Return whether a content type is supported by the pipeline."""

        return str(content_type).strip().lower() in self.supported_content_types

    def default_generation_setting(self, key: str, fallback: Any | None = None) -> Any:
        """Return a generation default value."""

        if key == "enable_live_generation":
            return self.enable_live_generation
        return self.generation_defaults.get(key, fallback)
