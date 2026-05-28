"""Tests for the markdown knowledge loader."""

from __future__ import annotations

from pathlib import Path

from src.core.knowledge_loader import KnowledgeLoader


def test_loader_initializes_correctly():
    loader = KnowledgeLoader()
    assert loader.brands_root.exists()


def test_brand_context_loads_for_wenzel_partner(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)

    assert bundle.brand == sample_brand_name
    assert bundle.brand_config
    assert bundle.knowledge_base
    assert bundle.detected_categories
    assert not bundle.warnings or isinstance(bundle.warnings, list)


def test_missing_brand_fails_gracefully():
    loader = KnowledgeLoader()
    bundle = loader.load_brand("missing_brand")

    assert bundle.brand == "missing_brand"
    assert bundle.brand_config == {}
    assert bundle.knowledge_base == {}
    assert bundle.warnings


def test_markdown_files_are_detected(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)

    assert bundle.files
    assert any(file_item.relative_path.endswith(".md") for file_item in bundle.files)
    assert any(file_item.category == "brand_config" for file_item in bundle.files)


def test_structured_context_includes_brand_config_and_knowledge_base(sample_brand_name):
    loader = KnowledgeLoader()
    bundle = loader.load_brand(sample_brand_name)

    assert isinstance(bundle.brand_config, dict)
    assert isinstance(bundle.knowledge_base, dict)
    assert "tone" in bundle.brand_config
    assert "market" in bundle.knowledge_base


def test_loader_supports_future_brands_without_hardcoded_brand_logic(tmp_path: Path):
    brands_root = tmp_path / "brands"
    future_brand = brands_root / "future_brand"
    (future_brand / "brand_config").mkdir(parents=True)
    (future_brand / "knowledge_base" / "market").mkdir(parents=True)
    (future_brand / "brand_config" / "tone.md").write_text("# Tone\n\nPremium but approachable.", encoding="utf-8")
    (future_brand / "knowledge_base" / "market" / "overview.md").write_text("# Market\n\nFuture brand market context.", encoding="utf-8")

    loader = KnowledgeLoader(brands_root=brands_root)
    bundle = loader.load_brand("future_brand")

    assert bundle.brand == "future_brand"
    assert bundle.brand_config
    assert bundle.knowledge_base
