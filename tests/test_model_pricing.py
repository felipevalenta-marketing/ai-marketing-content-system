from __future__ import annotations

from src.tracking.model_pricing import get_model_pricing, has_model_pricing, list_supported_pricing_models, normalize_model_name


def test_model_pricing_lookup_returns_registry_entry() -> None:
    pricing = get_model_pricing("openai", "gpt-4o-mini")
    assert pricing["provider"] == "openai"
    assert pricing["model"] == "gpt-4o-mini"
    assert "pricing_found" in pricing


def test_model_pricing_helpers_are_stable() -> None:
    assert normalize_model_name(" GPT-4O Mini ") == "gpt-4o-mini"
    assert has_model_pricing("openai", "gpt-4o-mini") is True
    assert isinstance(list_supported_pricing_models(), list)
