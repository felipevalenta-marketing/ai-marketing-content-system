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
    supported_platforms: tuple[str, ...] = DEFAULT_SUPPORTED_PLATFORMS
    supported_content_types: tuple[str, ...] = DEFAULT_SUPPORTED_CONTENT_TYPES
    export_formats: tuple[str, ...] = ("markdown", "json")
    output_root: str = "outputs"
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
