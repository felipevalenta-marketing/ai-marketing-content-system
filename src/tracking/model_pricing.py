"""Centralized model pricing registry."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import os

from src.reporting.report_metrics import safe_text


def normalize_model_name(model: str) -> str:
    """Normalize a model name for registry lookups."""

    return safe_text(model, limit=120).strip().lower().replace(" ", "-")


def _utc_today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _pricing_record(
    *,
    provider: str,
    model: str,
    currency: str = "USD",
    input_per_1m: float = 0.0,
    output_per_1m: float = 0.0,
    cached_input_per_1m: float = 0.0,
    pricing_source: str = "configurable",
    pricing_version: str = "local_default",
    effective_date: str | None = None,
    notes: str = "Update manually from official provider pricing.",
    pricing_found: bool = False,
) -> dict[str, Any]:
    return {
        "provider": safe_text(provider, limit=80).lower(),
        "model": normalize_model_name(model),
        "currency": currency,
        "input_per_1m": float(input_per_1m),
        "output_per_1m": float(output_per_1m),
        "cached_input_per_1m": float(cached_input_per_1m),
        "pricing_source": pricing_source,
        "pricing_version": pricing_version,
        "effective_date": effective_date or _utc_today_iso(),
        "notes": notes,
        "pricing_found": bool(pricing_found),
    }


_DEFAULT_MODEL = os.getenv("OPENAI_MODEL_DEFAULT", "gpt-4o-mini")

MODEL_PRICING_REGISTRY: dict[str, dict[str, dict[str, Any]]] = {
    "openai": {
        "gpt-4o-mini": _pricing_record(
            provider="openai",
            model="gpt-4o-mini",
            notes="Pricing not verified locally; update from official OpenAI pricing.",
            pricing_version="local_default",
            pricing_found=False,
        ),
        "gpt-4o": _pricing_record(
            provider="openai",
            model="gpt-4o",
            notes="Pricing not verified locally; update from official OpenAI pricing.",
            pricing_version="local_default",
            pricing_found=False,
        ),
    },
    "anthropic": {},
    "google": {},
    "grok": {},
    "local": {},
}

if normalize_model_name(_DEFAULT_MODEL) not in MODEL_PRICING_REGISTRY.get("openai", {}):
    MODEL_PRICING_REGISTRY["openai"][normalize_model_name(_DEFAULT_MODEL)] = _pricing_record(
        provider="openai",
        model=_DEFAULT_MODEL,
        notes="Default model registered from environment without verified pricing.",
        pricing_version="local_default",
        pricing_found=False,
    )


def get_model_pricing(provider: str, model: str) -> dict[str, Any]:
    """Lookup pricing for a provider/model combination."""

    normalized_provider = safe_text(provider, limit=80).lower() or "unknown"
    normalized_model = normalize_model_name(model)
    provider_registry = MODEL_PRICING_REGISTRY.get(normalized_provider, {})
    record = provider_registry.get(normalized_model)
    if record:
        return dict(record)
    return _pricing_record(
        provider=normalized_provider,
        model=normalized_model,
        notes="Pricing not found for provider/model.",
        pricing_source="unknown",
        pricing_version="unknown",
        pricing_found=False,
    )


def has_model_pricing(provider: str, model: str) -> bool:
    """Return whether the registry has a pricing entry for a model."""

    normalized_provider = safe_text(provider, limit=80).lower() or "unknown"
    normalized_model = normalize_model_name(model)
    return normalized_model in MODEL_PRICING_REGISTRY.get(normalized_provider, {})


def list_supported_pricing_models() -> list[dict[str, Any]]:
    """Return a flat list of registered pricing entries."""

    records: list[dict[str, Any]] = []
    for provider, models in MODEL_PRICING_REGISTRY.items():
        for model, pricing in models.items():
            record = dict(pricing)
            record["provider"] = provider
            record["model"] = model
            records.append(record)
    return records
