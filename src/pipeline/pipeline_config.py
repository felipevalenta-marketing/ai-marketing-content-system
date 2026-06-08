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
    "facebook_post",
    "linkedin_post",
    "ad_copy",
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


def _env_int(name: str, default: int) -> int:
    """Read an integer value from the environment safely."""

    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value.strip())
    except (TypeError, ValueError):
        return default


def _env_csv(name: str, default: list[str]) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None:
        return list(default)
    values = [item.strip() for item in raw_value.split(",")]
    cleaned = [item for item in values if item]
    return cleaned or list(default)


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration for the generation pipeline."""

    brands_root: str = "brands"
    app_env: str = field(default_factory=lambda: os.getenv("APP_ENV", "development").strip() or "development")
    api_host: str = field(default_factory=lambda: os.getenv("API_HOST", "127.0.0.1").strip() or "127.0.0.1")
    api_port: int = field(default_factory=lambda: _env_int("API_PORT", 8000))
    cors_origins: list[str] = field(default_factory=lambda: _env_csv("CORS_ORIGINS", ["http://127.0.0.1:5173", "http://localhost:5173", "http://localhost:3000"]))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "info").strip() or "info")
    default_brand: str = field(default_factory=lambda: os.getenv("DEFAULT_BRAND", "wenzel_partner"))
    enable_multi_brand_management: bool = field(default_factory=lambda: _env_flag("ENABLE_MULTI_BRAND_MANAGEMENT", True))
    brand_root: str = field(default_factory=lambda: os.getenv("BRAND_ROOT", "brands"))
    require_valid_brand: bool = field(default_factory=lambda: _env_flag("REQUIRE_VALID_BRAND", True))
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
    enable_persistence: bool = field(default_factory=lambda: _env_flag("ENABLE_PERSISTENCE", False))
    persist_generations: bool = field(default_factory=lambda: _env_flag("PERSIST_GENERATIONS", True))
    persist_reports: bool = field(default_factory=lambda: _env_flag("PERSIST_REPORTS", True))
    persist_tracking: bool = field(default_factory=lambda: _env_flag("PERSIST_TRACKING", True))
    persist_markdown: bool = field(default_factory=lambda: _env_flag("PERSIST_MARKDOWN", False))
    storage_overwrite: bool = field(default_factory=lambda: _env_flag("STORAGE_OVERWRITE", False))
    enable_token_tracking: bool = field(default_factory=lambda: _env_flag("ENABLE_TOKEN_TRACKING", True))
    enable_token_estimation: bool = field(default_factory=lambda: _env_flag("ENABLE_TOKEN_ESTIMATION", True))
    track_input_tokens: bool = field(default_factory=lambda: _env_flag("TRACK_INPUT_TOKENS", _env_flag("TRACK_PROMPT_TOKENS", True)))
    track_output_tokens: bool = field(default_factory=lambda: _env_flag("TRACK_OUTPUT_TOKENS", _env_flag("TRACK_COMPLETION_TOKENS", True)))
    enable_cost_tracking: bool = field(default_factory=lambda: _env_flag("ENABLE_COST_TRACKING", True))
    enable_cost_estimation: bool = field(default_factory=lambda: _env_flag("ENABLE_COST_ESTIMATION", True))
    default_cost_currency: str = field(default_factory=lambda: os.getenv("DEFAULT_COST_CURRENCY", "USD"))
    cost_round_decimals: int = field(default_factory=lambda: _env_int("COST_ROUND_DECIMALS", 6))
    enable_workflow_orchestration: bool = field(default_factory=lambda: _env_flag("ENABLE_WORKFLOW_ORCHESTRATION", False))
    default_workflow_type: str = field(default_factory=lambda: os.getenv("DEFAULT_WORKFLOW_TYPE", "single_content_generation"))
    workflow_persistence_enabled: bool = field(default_factory=lambda: _env_flag("WORKFLOW_PERSISTENCE_ENABLED", True))
    workflow_stop_on_critical_failure: bool = field(default_factory=lambda: _env_flag("WORKFLOW_STOP_ON_CRITICAL_FAILURE", True))
    workflow_continue_on_warnings: bool = field(default_factory=lambda: _env_flag("WORKFLOW_CONTINUE_ON_WARNINGS", True))
    enable_image_prompt_engine: bool = field(default_factory=lambda: _env_flag("ENABLE_IMAGE_PROMPT_ENGINE", False))
    enable_cinematic_enhancement: bool = field(default_factory=lambda: _env_flag("ENABLE_CINEMATIC_ENHANCEMENT", True))
    enable_negative_prompts: bool = field(default_factory=lambda: _env_flag("ENABLE_NEGATIVE_PROMPTS", True))
    enable_video_script_engine: bool = field(default_factory=lambda: _env_flag("ENABLE_VIDEO_SCRIPT_ENGINE", False))
    enable_storyboard_generation: bool = field(default_factory=lambda: _env_flag("ENABLE_STORYBOARD_GENERATION", True))
    enable_creative_direction_engine: bool = field(default_factory=lambda: _env_flag("ENABLE_CREATIVE_DIRECTION_ENGINE", False))
    enable_markdown_reports: bool = field(default_factory=lambda: _env_flag("ENABLE_MARKDOWN_REPORTS", True))
    enable_markdown_report_export: bool = field(default_factory=lambda: _env_flag("ENABLE_MARKDOWN_REPORT_EXPORT", True))
    default_markdown_report_type: str = field(default_factory=lambda: os.getenv("DEFAULT_MARKDOWN_REPORT_TYPE", "execution_report"))
    markdown_report_output_root: str = field(default_factory=lambda: os.getenv("MARKDOWN_REPORT_OUTPUT_ROOT", "outputs/reports/markdown"))
    enable_api_layer: bool = field(default_factory=lambda: _env_flag("ENABLE_API_LAYER", True))
    enable_frontend_demo: bool = field(default_factory=lambda: _env_flag("ENABLE_FRONTEND_DEMO", True))
    api_debug: bool = field(default_factory=lambda: _env_flag("API_DEBUG", False))
    enable_authentication: bool = field(default_factory=lambda: _env_flag("ENABLE_AUTHENTICATION", True))
    jwt_expiration_hours: int = field(default_factory=lambda: _env_int("JWT_EXPIRATION_HOURS", 24))
    user_storage_path: str = field(default_factory=lambda: os.getenv("USER_STORAGE_PATH", "data/users"))
    enable_rbac: bool = field(default_factory=lambda: _env_flag("ENABLE_RBAC", True))
    default_user_role: str = field(default_factory=lambda: os.getenv("DEFAULT_USER_ROLE", "viewer"))
    first_user_admin: bool = field(default_factory=lambda: _env_flag("FIRST_USER_ADMIN", True))
    enable_organizations: bool = field(default_factory=lambda: _env_flag("ENABLE_ORGANIZATIONS", True))
    enable_teams: bool = field(default_factory=lambda: _env_flag("ENABLE_TEAMS", True))
    max_organizations: int = field(default_factory=lambda: _env_int("MAX_ORGANIZATIONS", 100))
    max_teams: int = field(default_factory=lambda: _env_int("MAX_TEAMS", 500))
    max_members_per_organization: int = field(default_factory=lambda: _env_int("MAX_MEMBERS_PER_ORGANIZATION", 1000))
    enable_analytics: bool = field(default_factory=lambda: _env_flag("ENABLE_ANALYTICS", True))
    analytics_default_type: str = field(default_factory=lambda: os.getenv("ANALYTICS_DEFAULT_TYPE", "executive_dashboard"))
    analytics_include_storage: bool = field(default_factory=lambda: _env_flag("ANALYTICS_INCLUDE_STORAGE", True))
    analytics_include_tokens: bool = field(default_factory=lambda: _env_flag("ANALYTICS_INCLUDE_TOKENS", True))
    analytics_include_costs: bool = field(default_factory=lambda: _env_flag("ANALYTICS_INCLUDE_COSTS", True))
    analytics_include_governance: bool = field(default_factory=lambda: _env_flag("ANALYTICS_INCLUDE_GOVERNANCE", True))
    enable_observability: bool = field(default_factory=lambda: _env_flag("ENABLE_OBSERVABILITY", True))
    enable_request_logging: bool = field(default_factory=lambda: _env_flag("ENABLE_REQUEST_LOGGING", True))
    enable_error_tracking: bool = field(default_factory=lambda: _env_flag("ENABLE_ERROR_TRACKING", True))
    enable_runtime_metrics: bool = field(default_factory=lambda: _env_flag("ENABLE_RUNTIME_METRICS", True))
    enable_workflow_monitoring: bool = field(default_factory=lambda: _env_flag("ENABLE_WORKFLOW_MONITORING", True))
    enable_security_hardening: bool = field(default_factory=lambda: _env_flag("ENABLE_SECURITY_HARDENING", True))
    enable_security_headers: bool = field(default_factory=lambda: _env_flag("ENABLE_SECURITY_HEADERS", True))
    enable_rate_limiting: bool = field(default_factory=lambda: _env_flag("ENABLE_RATE_LIMITING", True))
    enable_secret_scanning: bool = field(default_factory=lambda: _env_flag("ENABLE_SECRET_SCANNING", True))
    enable_dependency_validation: bool = field(default_factory=lambda: _env_flag("ENABLE_DEPENDENCY_VALIDATION", True))
    enable_input_sanitization: bool = field(default_factory=lambda: _env_flag("ENABLE_INPUT_SANITIZATION", True))
    enable_output_sanitization: bool = field(default_factory=lambda: _env_flag("ENABLE_OUTPUT_SANITIZATION", True))
    security_request_size_limit_kb: int = field(default_factory=lambda: _env_int("REQUEST_SIZE_LIMIT_KB", 256))
    anonymous_rate_limit_per_hour: int = field(default_factory=lambda: _env_int("ANONYMOUS_RATE_LIMIT_PER_HOUR", 100))
    authenticated_rate_limit_per_hour: int = field(default_factory=lambda: _env_int("AUTHENTICATED_RATE_LIMIT_PER_HOUR", 1000))
    admin_rate_limit_per_hour: int = field(default_factory=lambda: _env_int("ADMIN_RATE_LIMIT_PER_HOUR", 5000))
    enable_ci_security_checks: bool = field(default_factory=lambda: _env_flag("ENABLE_CI_SECURITY_CHECKS", False))
    enable_release_validation: bool = field(default_factory=lambda: _env_flag("ENABLE_RELEASE_VALIDATION", False))
    enable_docker_validation: bool = field(default_factory=lambda: _env_flag("ENABLE_DOCKER_VALIDATION", False))
    enable_mvp_acceptance: bool = field(default_factory=lambda: _env_flag("ENABLE_MVP_ACCEPTANCE", True))
    enable_readiness_scoring: bool = field(default_factory=lambda: _env_flag("ENABLE_READINESS_SCORING", True))
    enable_release_certification: bool = field(default_factory=lambda: _env_flag("ENABLE_RELEASE_CERTIFICATION", True))
    enable_maturity_scoring: bool = field(default_factory=lambda: _env_flag("ENABLE_MATURITY_SCORING", True))
    observability_log_level: str = field(default_factory=lambda: os.getenv("OBSERVABILITY_LOG_LEVEL", os.getenv("LOG_LEVEL", "info")).strip() or "info")
    recent_error_limit: int = field(default_factory=lambda: _env_int("RECENT_ERROR_LIMIT", 50))
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
    storage_root: str = field(default_factory=lambda: os.getenv("STORAGE_ROOT", "data"))
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
