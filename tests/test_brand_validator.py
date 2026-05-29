from __future__ import annotations

from pathlib import Path

from src.brands.brand_validator import validate_brand


def test_brand_validator_detects_secrets_in_brand_json(tmp_path: Path) -> None:
    brand_root = tmp_path / "brands"
    brand = brand_root / "safe_brand"
    brand.mkdir(parents=True)
    (brand / "audience.md").write_text("Audience", encoding="utf-8")
    (brand / "brand.json").write_text('{"brand_id":"safe_brand","api_key":"sk-test-secret"}', encoding="utf-8")

    result = validate_brand("safe_brand", root_path=str(brand_root))

    assert result["valid"] is False
    assert any("secret" in error.lower() for error in result["errors"])


def test_brand_validator_rejects_path_traversal(tmp_path: Path) -> None:
    brand_root = tmp_path / "brands"
    brand_root.mkdir()

    result = validate_brand("../bad", root_path=str(brand_root))

    assert result["valid"] is False
    assert any("filesystem safe" in error.lower() for error in result["errors"])
