"""Configuration settings for the end-to-end generation pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        """Fallback no-op when python-dotenv is unavailable."""

        return False


load_dotenv()


DEFAULT_SUPPORTED_CONTENT_TYPES = (
    "instagram_post",
    "instagram_reel",
    "property_description",
    "image_prompt",
    "video_prompt",
    "video_script",
    "creative_direction",
    "campaign_asset",
)

DEFAULT_SUPPORTED_IMAGE_PROMPT_TYPES = (
    "property_exterior",
    "property_interior",
    "lifestyle_scene",
    "architectural_detail",
    "drone_view",
    "neighborhood_scene",
    "reform_potential",
    "luxury_listing",
    "social_media_visual",
    "campaign_hero_image",
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


def _env_flag(name: str, default: bool = False) -> bool:
    """Read a boolean feature flag from the environment.

    Supported truthy values are ``true``, ``1``, ``yes``, and ``on``.
    Any other value falls back to ``default``.
    """

    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return default


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration for the generation pipeline."""

    brands_root: str = "brands"
    default_brand: str = "wenzel_partner"
    default_platform: str = "instagram"
    default_content_type: str = "instagram_post"
    enable_live_generation: bool = field(default_factory=lambda: _env_flag("ENABLE_LIVE_GENERATION", True))
    enable_output_formatting: bool = field(default_factory=lambda: _env_flag("ENABLE_OUTPUT_FORMATTING", True))
    enable_output_validation: bool = field(default_factory=lambda: _env_flag("ENABLE_OUTPUT_VALIDATION", True))
    enable_rendering: bool = field(default_factory=lambda: _env_flag("ENABLE_RENDERING", True))
    enable_export: bool = field(default_factory=lambda: _env_flag("ENABLE_EXPORT", False))
    enable_platform_adaptation: bool = field(default_factory=lambda: _env_flag("ENABLE_PLATFORM_ADAPTATION", False))
    enable_governance_validation: bool = field(default_factory=lambda: _env_flag("ENABLE_GOVERNANCE_VALIDATION", False))
    enable_campaign_composition: bool = field(default_factory=lambda: _env_flag("ENABLE_CAMPAIGN_COMPOSITION", False))
    enable_campaign_export: bool = field(default_factory=lambda: _env_flag("ENABLE_CAMPAIGN_EXPORT", False))
    enable_asset_coordination: bool = field(default_factory=lambda: _env_flag("ENABLE_ASSET_COORDINATION", False))
    enable_asset_export: bool = field(default_factory=lambda: _env_flag("ENABLE_ASSET_EXPORT", False))
    enable_reporting: bool = field(default_factory=lambda: _env_flag("ENABLE_REPORTING", False))
    enable_report_export: bool = field(default_factory=lambda: _env_flag("ENABLE_REPORT_EXPORT", False))
    enable_token_tracking: bool = field(default_factory=lambda: _env_flag("ENABLE_TOKEN_TRACKING", True))
    enable_token_estimation: bool = field(default_factory=lambda: _env_flag("ENABLE_TOKEN_ESTIMATION", True))
    track_input_tokens: bool = field(default_factory=lambda: _env_flag("TRACK_INPUT_TOKENS", _env_flag("TRACK_PROMPT_TOKENS", True)))
    track_output_tokens: bool = field(default_factory=lambda: _env_flag("TRACK_OUTPUT_TOKENS", _env_flag("TRACK_COMPLETION_TOKENS", True)))
    enable_image_prompt_engine: bool = field(default_factory=lambda: _env_flag("ENABLE_IMAGE_PROMPT_ENGINE", False))
    enable_cinematic_enhancement: bool = field(default_factory=lambda: _env_flag("ENABLE_CINEMATIC_ENHANCEMENT", True))
    enable_negative_prompts: bool = field(default_factory=lambda: _env_flag("ENABLE_NEGATIVE_PROMPTS", True))
    enable_video_script_engine: bool = field(default_factory=lambda: _env_flag("ENABLE_VIDEO_SCRIPT_ENGINE", False))
    enable_storyboard_generation: bool = field(default_factory=lambda: _env_flag("ENABLE_STORYBOARD_GENERATION", True))
    enable_creative_direction_engine: bool = field(default_factory=lambda: _env_flag("ENABLE_CREATIVE_DIRECTION_ENGINE", False))
    governance_min_score: float = 70.0
    reject_on_critical_safety_error: bool = True
    supported_platforms: tuple[str, ...] = DEFAULT_SUPPORTED_PLATFORMS
    supported_content_types: tuple[str, ...] = DEFAULT_SUPPORTED_CONTENT_TYPES
    supported_image_prompt_types: tuple[str, ...] = DEFAULT_SUPPORTED_IMAGE_PROMPT_TYPES
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
    default_visual_style: str = field(default_factory=lambda: os.getenv("DEFAULT_VISUAL_STYLE", "mediterranean_lifestyle"))
    default_image_aspect_ratio: str = field(default_factory=lambda: os.getenv("DEFAULT_IMAGE_ASPECT_RATIO", "4:5"))
    default_video_duration: str = field(default_factory=lambda: os.getenv("DEFAULT_VIDEO_DURATION", "30s"))
    default_video_type: str = field(default_factory=lambda: os.getenv("DEFAULT_VIDEO_TYPE", "instagram_reel"))
    default_creative_direction_type: str = field(default_factory=lambda: os.getenv("DEFAULT_CREATIVE_DIRECTION_TYPE", "campaign_visual_direction"))
    default_visual_identity: str = field(default_factory=lambda: os.getenv("DEFAULT_VISUAL_IDENTITY", "mediterranean_luxury"))
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
