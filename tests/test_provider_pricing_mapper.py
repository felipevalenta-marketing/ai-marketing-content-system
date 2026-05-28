from __future__ import annotations

from src.tracking.provider_pricing_mapper import ProviderPricingMapper


def test_provider_pricing_mapper_normalizes_aliases() -> None:
    mapper = ProviderPricingMapper()
    assert mapper.normalize_provider_name("Claude") == "anthropic"
    assert mapper.normalize_provider_name("Gemini") == "google"
    assert mapper.normalize_model_name(" GPT-4O ") == "gpt-4o"


def test_provider_pricing_mapper_lookup_returns_pricing_dict() -> None:
    mapper = ProviderPricingMapper()
    pricing = mapper.lookup_pricing("openai", "gpt-4o-mini")
    assert pricing["provider"] == "openai"
    assert pricing["model"] == "gpt-4o-mini"
