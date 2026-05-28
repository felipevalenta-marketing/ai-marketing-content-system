"""Tests for LLM routing."""

from __future__ import annotations

from src.llm.llm_router import LLMRouter


def test_instagram_post_routes_to_expected_model():
    router = LLMRouter()
    decision = router.route("instagram_post")

    assert decision.provider == "openai"
    assert decision.model_name == "gpt-4o-mini"


def test_image_prompt_routes_to_expected_model():
    router = LLMRouter()
    decision = router.route("image_prompt")

    assert decision.provider == "openai"
    assert decision.model_name == "gpt-4o"


def test_seo_or_campaign_content_routes_to_higher_capability_model():
    router = LLMRouter()
    decision = router.route("seo_page")

    assert decision.model_name == "gpt-4o"


def test_unsupported_content_type_uses_fallback():
    router = LLMRouter()
    decision = router.route("unsupported_content")

    assert decision.provider == "openai"
    assert decision.model_name


def test_provider_abstraction_remains_intact():
    router = LLMRouter()
    decision = router.route("instagram_post", provider="claude")

    assert decision.provider == "claude"
    assert decision.model_name == "gpt-4o-mini"
