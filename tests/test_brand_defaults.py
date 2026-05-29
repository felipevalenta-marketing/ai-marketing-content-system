from __future__ import annotations

from src.brands.brand_defaults import get_brand_defaults, list_brand_defaults, merge_brand_defaults, normalize_brand_defaults


def test_brand_defaults_merge_and_lookup() -> None:
    merged = merge_brand_defaults(
        {"default_platform": "linkedin", "default_language": "es"},
        {"default_content_type": "linkedin_post", "default_campaign_type": "brand_awareness"},
    )

    assert merged["default_platform"] == "linkedin"
    assert merged["default_content_type"] == "linkedin_post"
    assert merged["default_campaign_type"] == "brand_awareness"
    assert merged["default_language"] == "es"


def test_brand_defaults_registry_includes_wenzel_partner() -> None:
    defaults = get_brand_defaults("wenzel_partner")
    registry = list_brand_defaults()

    assert defaults["display_name"] == "Wenzel & Partner"
    assert "wenzel_partner" in registry
    assert normalize_brand_defaults(defaults)["default_platform"] == "instagram"
