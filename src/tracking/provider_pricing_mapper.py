"""Provider/model normalization helpers for pricing lookup."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_text
from src.tracking.model_pricing import get_model_pricing, normalize_model_name


PROVIDER_ALIASES = {
    "openai": "openai",
    "anthropic": "anthropic",
    "claude": "anthropic",
    "google": "google",
    "gemini": "google",
    "grok": "grok",
    "xai": "grok",
    "local": "local",
    "llama": "local",
}


class ProviderPricingMapper:
    """Normalize provider/model identifiers into pricing registry lookups."""

    def normalize_provider_name(self, provider: str) -> str:
        """Return a canonical provider name."""

        candidate = safe_text(provider, limit=80).lower()
        return PROVIDER_ALIASES.get(candidate, candidate or "unknown")

    def normalize_model_name(self, model: str) -> str:
        """Return a canonical model name."""

        return normalize_model_name(model)

    def lookup_pricing(self, provider: str, model: str) -> dict[str, Any]:
        """Return a pricing table record for a provider/model pair."""

        normalized_provider = self.normalize_provider_name(provider)
        normalized_model = self.normalize_model_name(model)
        pricing = get_model_pricing(normalized_provider, normalized_model)
        pricing["provider"] = normalized_provider
        pricing["model"] = normalized_model
        return pricing

    def supports_provider(self, provider: str) -> bool:
        """Return whether a provider is supported by the mapper."""

        return self.normalize_provider_name(provider) in PROVIDER_ALIASES.values()
