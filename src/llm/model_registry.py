"""Centralized model metadata for provider-agnostic routing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import os

try:
    import tiktoken
except Exception:  # pragma: no cover - optional dependency
    tiktoken = None

from src.utils.file_utils import normalize_key


def normalize_model_name(value: str) -> str:
    """Normalize a model name while preserving provider-specific punctuation."""

    return str(value).strip().lower().replace(" ", "-")


@dataclass(frozen=True)
class ModelMetadata:
    """Describe a model entry in the registry."""

    provider: str
    model_name: str
    default_temperature: float
    supported_content_types: list[str]
    max_output_tokens: int
    pricing_input_per_1k: float | None = None
    pricing_output_per_1k: float | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Backward-compatible alias for the model name."""

        return self.model_name

    def to_dict(self) -> dict[str, Any]:
        """Serialize the model metadata."""

        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "name": self.model_name,
            "default_temperature": self.default_temperature,
            "supported_content_types": self.supported_content_types,
            "max_output_tokens": self.max_output_tokens,
            "pricing_input_per_1k": self.pricing_input_per_1k,
            "pricing_output_per_1k": self.pricing_output_per_1k,
            "notes": self.notes,
        }


MODEL_REGISTRY: dict[str, ModelMetadata] = {
    "gpt-4o-mini": ModelMetadata(
        provider="openai",
        model_name="gpt-4o-mini",
        default_temperature=0.7,
        supported_content_types=[
            "instagram_post",
            "instagram_reel",
            "facebook_post",
            "property_description",
            "ad_copy",
            "creative_direction",
        ],
        max_output_tokens=1200,
        notes=["Fast default for concise marketing content."],
    ),
    "gpt-4o": ModelMetadata(
        provider="openai",
        model_name="gpt-4o",
        default_temperature=0.6,
        supported_content_types=[
            "seo_page",
            "image_prompt",
            "video_prompt",
            "video_script",
            "campaign_pack",
            "linkedin_post",
            "neighborhood_story",
            "relocation_content",
            "email_marketing",
        ],
        max_output_tokens=2400,
        notes=["Balanced default for longer-form and visual direction prompts."],
    ),
}


DEFAULT_MODEL_BY_CONTENT_TYPE: dict[str, str] = {
    "instagram_post": "gpt-4o-mini",
    "instagram_reel": "gpt-4o-mini",
    "facebook_post": "gpt-4o-mini",
    "property_description": "gpt-4o-mini",
    "ad_copy": "gpt-4o-mini",
    "creative_direction": "gpt-4o-mini",
    "seo_page": "gpt-4o",
    "image_prompt": "gpt-4o",
    "video_prompt": "gpt-4o",
    "video_script": "gpt-4o",
    "campaign_pack": "gpt-4o",
    "linkedin_post": "gpt-4o",
    "neighborhood_story": "gpt-4o",
    "relocation_content": "gpt-4o",
    "email_marketing": "gpt-4o",
}


SUPPORTED_PROVIDERS = ("openai", "claude", "gemini", "local")


def get_env_default_model() -> str:
    """Read the default model name from the environment."""

    return normalize_model_name(os.getenv("OPENAI_MODEL_DEFAULT", "gpt-4o-mini"))


def get_env_default_temperature() -> float:
    """Read the default temperature from the environment."""

    raw_value = os.getenv("OPENAI_TEMPERATURE", "0.7")
    try:
        return float(raw_value)
    except ValueError:
        return 0.7


def get_env_default_max_output_tokens() -> int:
    """Read the default output token limit from the environment."""

    raw_value = os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "1200")
    try:
        return int(raw_value)
    except ValueError:
        return 1200


def get_model_metadata(model_name: str) -> ModelMetadata:
    """Return model metadata or a generic fallback entry."""

    key = normalize_model_name(model_name)
    metadata = MODEL_REGISTRY.get(key)
    if metadata is not None:
        return metadata

    return ModelMetadata(
        provider="openai",
        model_name=key or "unknown",
        default_temperature=get_env_default_temperature(),
        supported_content_types=["generic"],
        max_output_tokens=get_env_default_max_output_tokens(),
        notes=["Fallback metadata entry."],
    )


def is_supported_model(model_name: str, provider: str | None = None) -> bool:
    """Return whether a model is explicitly registered."""

    key = normalize_model_name(model_name)
    metadata = MODEL_REGISTRY.get(key)
    if metadata is None:
        return False
    if provider and normalize_key(metadata.provider) != normalize_key(provider):
        return False
    return True


def list_models(provider: str | None = None) -> list[dict[str, Any]]:
    """Return the registry entries, optionally filtered by provider."""

    entries = [metadata.to_dict() for metadata in MODEL_REGISTRY.values()]
    if provider:
        provider_key = normalize_key(provider)
        entries = [entry for entry in entries if normalize_key(str(entry["provider"])) == provider_key]
    return sorted(entries, key=lambda item: item["model_name"])


def resolve_model_for_content_type(
    content_type: str,
    provider: str = "openai",
    preferred_model: str | None = None,
) -> ModelMetadata:
    """Resolve the preferred model for a content type."""

    content_key = normalize_key(content_type)
    provider_key = normalize_key(provider or "openai") or "openai"

    candidate_name = normalize_model_name(preferred_model) if preferred_model else DEFAULT_MODEL_BY_CONTENT_TYPE.get(content_key)
    if candidate_name is None:
        candidate_name = get_env_default_model()

    metadata = get_model_metadata(candidate_name)
    if normalize_key(metadata.provider) != provider_key:
        return ModelMetadata(
            provider=provider_key,
            model_name=metadata.model_name,
            default_temperature=metadata.default_temperature,
            supported_content_types=metadata.supported_content_types,
            max_output_tokens=metadata.max_output_tokens,
            pricing_input_per_1k=metadata.pricing_input_per_1k,
            pricing_output_per_1k=metadata.pricing_output_per_1k,
            notes=metadata.notes + ["Provider override applied."],
        )
    return metadata


def estimate_tokens(text: str, model_name: str | None = None) -> int:
    """Estimate tokens for a string payload."""

    if not text:
        return 0

    model = model_name or get_env_default_model()
    if tiktoken is not None:
        try:
            encoding = tiktoken.encoding_for_model(model)
        except Exception:  # pragma: no cover - model lookup fallback
            encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))

    return max(1, len(text) // 4)
