from __future__ import annotations

from pathlib import Path

from src.brands.brand_manager import BrandManager


def _make_brand(root: Path, brand_id: str, *, active: bool = True, config: str | None = None, complete: bool = True) -> Path:
    brand = root / brand_id
    brand.mkdir(parents=True)
    if complete:
        for name in ("audience.md", "positioning.md", "tone_of_voice.md", "content_rules.md"):
            (brand / name).write_text(f"{name} for {brand_id}", encoding="utf-8")
    if config is not None:
        (brand / "brand.json").write_text(config, encoding="utf-8")
    return brand


def test_brand_manager_merges_brand_json_and_reports_health(tmp_path: Path) -> None:
    brand_root = tmp_path / "brands"
    brand_root.mkdir()
    _make_brand(
        brand_root,
        "wenzel_partner",
        config='{"brand_id":"wenzel_partner","display_name":"Wenzel & Partner","default_platform":"linkedin","default_content_type":"linkedin_post","default_campaign_type":"brand_awareness","default_language":"en","active":true}',
    )

    manager = BrandManager(brand_root=str(brand_root))
    profile = manager.get_brand("wenzel_partner")
    health = manager.get_brand_health("wenzel_partner")

    assert profile["success"] is True
    assert profile["status"] == "active"
    assert profile["configuration_present"] is True
    assert profile["defaults"]["default_platform"] == "linkedin"
    assert profile["health_score"] >= 80
    assert health["health_status"] == "healthy"


def test_brand_manager_filters_active_inactive_and_invalid(tmp_path: Path) -> None:
    brand_root = tmp_path / "brands"
    brand_root.mkdir()
    _make_brand(brand_root, "active_brand", active=True, config='{"brand_id":"active_brand","active":true}')
    _make_brand(brand_root, "inactive_brand", active=False, config='{"brand_id":"inactive_brand","active":false}')
    _make_brand(brand_root, "incomplete_brand", complete=False)
    _make_brand(brand_root, "invalid_brand", complete=True, config='{"brand_id":"invalid_brand",')

    manager = BrandManager(brand_root=str(brand_root))
    all_brands = manager.list_brands()
    active_only = manager.list_brands(active_only=True)
    include_invalid = manager.list_brands(include_invalid=True)

    assert all_brands["count"] >= 3
    assert all(brand["status"] != "invalid" for brand in all_brands["brands"])
    assert all(brand["status"] == "active" for brand in active_only["brands"])
    assert any(brand["status"] == "invalid" for brand in include_invalid["brands"])
