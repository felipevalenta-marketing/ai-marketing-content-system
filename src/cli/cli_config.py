"""Safe CLI configuration helpers."""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path
from typing import Any
import os

from src.llm.model_registry import (
    get_env_default_max_output_tokens,
    get_env_default_model,
    get_env_default_temperature,
)
from src.pipeline.pipeline_config import PipelineConfig


def get_project_root() -> Path:
    """Return the repository root path."""

    return Path(__file__).resolve().parents[2]


def parse_csv_list(value: str | None, default: list[str] | None = None) -> list[str]:
    """Parse a comma-separated CLI argument into a cleaned list."""

    if value is None:
        return list(default or [])

    items = [item.strip() for item in value.split(",")]
    cleaned = [item for item in items if item]
    if cleaned:
        return cleaned
    return list(default or [])


def has_openai_api_key() -> bool:
    """Return whether an OpenAI API key is present without exposing it."""

    return bool(os.getenv("OPENAI_API_KEY", "").strip())


def build_feature_flags() -> dict[str, Any]:
    """Summarize pipeline feature flags for safe inspection."""

    pipeline_config = PipelineConfig()
    return {
        "enable_live_generation": pipeline_config.enable_live_generation,
        "enable_output_formatting": pipeline_config.enable_output_formatting,
        "enable_output_validation": pipeline_config.enable_output_validation,
        "enable_rendering": pipeline_config.enable_rendering,
        "enable_export": pipeline_config.enable_export,
        "enable_platform_adaptation": pipeline_config.enable_platform_adaptation,
        "enable_governance_validation": pipeline_config.enable_governance_validation,
        "enable_campaign_composition": pipeline_config.enable_campaign_composition,
        "enable_campaign_export": pipeline_config.enable_campaign_export,
        "enable_asset_coordination": pipeline_config.enable_asset_coordination,
        "enable_asset_export": pipeline_config.enable_asset_export,
        "enable_reporting": pipeline_config.enable_reporting,
        "enable_report_export": pipeline_config.enable_report_export,
        "enable_image_prompt_engine": pipeline_config.enable_image_prompt_engine,
        "enable_cinematic_enhancement": pipeline_config.enable_cinematic_enhancement,
        "enable_negative_prompts": pipeline_config.enable_negative_prompts,
    }


def build_module_presence() -> dict[str, bool]:
    """Report whether the major runtime modules are importable."""

    module_names = [
        "src.cli",
        "src.core",
        "src.prompts",
        "src.llm",
        "src.output",
        "src.adapters",
        "src.governance",
        "src.campaigns",
        "src.assets",
        "src.reporting",
        "src.pipeline",
        "openai",
        "dotenv",
    ]
    return {name: find_spec(name) is not None for name in module_names}


def build_project_paths() -> dict[str, str]:
    """Return important project paths for safe CLI inspection."""

    root = get_project_root()
    return {
        "root": str(root),
        "src": str(root / "src"),
        "brands": str(root / "brands"),
        "outputs": str(root / "outputs"),
        "tests": str(root / "tests"),
        "config": str(root / "config"),
        "readme": str(root / "README.md"),
    }


def build_safe_config_summary() -> dict[str, Any]:
    """Return a safe summary of runtime configuration."""

    pipeline_config = PipelineConfig()
    return {
        "app_env": os.getenv("APP_ENV", "development").strip() or "development",
        "openai_api_key_present": has_openai_api_key(),
        "default_model": get_env_default_model(),
        "default_temperature": get_env_default_temperature(),
        "default_max_output_tokens": get_env_default_max_output_tokens(),
        "feature_flags": build_feature_flags(),
        "supported_platforms": list(pipeline_config.supported_platforms),
        "supported_content_types": list(pipeline_config.supported_content_types),
        "default_brand": pipeline_config.default_brand,
        "default_platform": pipeline_config.default_platform,
        "default_content_type": pipeline_config.default_content_type,
        "default_campaign_type": pipeline_config.default_campaign_type,
        "default_visual_style": pipeline_config.default_visual_style,
        "default_image_aspect_ratio": pipeline_config.default_image_aspect_ratio,
        "default_asset_types": list(pipeline_config.default_asset_types),
        "export_defaults": {
            "output_root": pipeline_config.output_root,
            "campaign_output_root": pipeline_config.campaign_output_root,
            "asset_output_root": pipeline_config.asset_output_root,
            "export_formats": list(pipeline_config.export_formats),
        },
        "paths": build_project_paths(),
        "available_modules": build_module_presence(),
    }
