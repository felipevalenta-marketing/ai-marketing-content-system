"""Tests for context assembly helpers."""

from __future__ import annotations

from src.core.context_builder import ContextBuilder
from src.core.knowledge_loader import KnowledgeLoader


def test_context_builder_assembles_structured_context(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)
    builder = ContextBuilder()

    context = builder.build_brand_context(bundle)

    assert context["brand"] == sample_brand_name
    assert isinstance(context["brand_config"], dict)
    assert isinstance(context["knowledge_base"], dict)
    assert isinstance(context["metadata"], dict)


def test_condensed_context_is_returned(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)
    builder = ContextBuilder()

    condensed = builder.condensed_context(bundle)

    assert isinstance(condensed, str)
    assert condensed.strip()


def test_category_context_works(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)
    builder = ContextBuilder()

    market_context = builder.get_market_context(bundle)
    neighborhood_context = builder.get_neighborhood_context(bundle, "santa_catalina")

    assert isinstance(market_context, str)
    assert isinstance(neighborhood_context, str)


def test_missing_category_returns_safe_fallback(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)
    builder = ContextBuilder()

    missing = builder.get_neighborhood_context(bundle, "missing_neighborhood")

    assert missing == ""


def test_context_metadata_is_preserved(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)
    builder = ContextBuilder()

    context = builder.build_brand_context(bundle)

    assert "raw_content" in context
    assert "normalized_content" in context
    assert "detected_categories" in context


def test_context_output_is_dictionary_based_and_reusable(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)
    builder = ContextBuilder()

    summary = builder.build_summarized_context(bundle)
    priority_layers = builder.build_priority_layers(bundle)

    assert isinstance(summary, dict)
    assert isinstance(priority_layers, dict)
    assert "brand_config" in priority_layers
    assert "content_rules" in priority_layers
