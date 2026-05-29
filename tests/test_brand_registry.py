from __future__ import annotations

from pathlib import Path

from src.brands.brand_registry import discover_brands, is_valid_brand_id, normalize_brand_id


def test_brand_registry_discovers_safe_brands(tmp_path: Path) -> None:
    brand_root = tmp_path / "brands"
    brand_root.mkdir()
    active_brand = brand_root / "active_brand"
    active_brand.mkdir()
    (active_brand / "audience.md").write_text("Audience", encoding="utf-8")
    (active_brand / "content_rules.md").write_text("Rules", encoding="utf-8")

    brands = discover_brands(str(brand_root))

    assert len(brands) == 1
    assert brands[0]["brand_id"] == "active_brand"
    assert normalize_brand_id("Wenzel & Partner") == "wenzel_and_partner"
    assert is_valid_brand_id("active_brand") is True
    assert is_valid_brand_id("../bad") is False


def test_brand_registry_ignores_hidden_and_unsafe_folders(tmp_path: Path) -> None:
    brand_root = tmp_path / "brands"
    brand_root.mkdir()
    (brand_root / ".hidden").mkdir()
    (brand_root / "safe_brand").mkdir()
    (brand_root / "safe_brand" / "audience.md").write_text("Audience", encoding="utf-8")

    brands = discover_brands(str(brand_root))

    assert [brand["brand_id"] for brand in brands] == ["safe_brand"]
