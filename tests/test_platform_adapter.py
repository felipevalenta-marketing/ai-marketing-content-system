"""Tests for deterministic platform adaptation."""

from __future__ import annotations

from src.adapters.platform_adapter import PlatformAdapter


def test_formatted_output_adapts_to_instagram(sample_formatted_output):
    adapter = PlatformAdapter()
    result = adapter.adapt({"content_type": "property_description", "formatted_output": sample_formatted_output, "metadata": {}}, ["instagram"])

    assert result["success"] is True
    assert "instagram" in result["platform_variants"]
    assert result["platform_variants"]["instagram"]["content"]["caption"]


def test_formatted_output_adapts_to_facebook(sample_formatted_output):
    adapter = PlatformAdapter()
    result = adapter.adapt({"content_type": "property_description", "formatted_output": sample_formatted_output, "metadata": {}}, ["facebook"])

    assert "facebook" in result["platform_variants"]
    assert result["platform_variants"]["facebook"]["content"]["post"]


def test_formatted_output_adapts_to_linkedin(sample_formatted_output):
    adapter = PlatformAdapter()
    result = adapter.adapt({"content_type": "property_description", "formatted_output": sample_formatted_output, "metadata": {}}, ["linkedin"])

    assert "linkedin" in result["platform_variants"]
    assert result["platform_variants"]["linkedin"]["content"]["headline"]


def test_formatted_output_adapts_to_email(sample_formatted_output):
    adapter = PlatformAdapter()
    result = adapter.adapt({"content_type": "property_description", "formatted_output": sample_formatted_output, "metadata": {}}, ["email"])

    email_content = result["platform_variants"]["email"]["content"]
    assert email_content["subject"]
    assert email_content["cta"]
    assert email_content.get("hashtags", []) == []


def test_formatted_output_adapts_to_website_listing(sample_formatted_output):
    adapter = PlatformAdapter()
    result = adapter.adapt({"content_type": "property_description", "formatted_output": sample_formatted_output, "metadata": {}}, ["website_listing"])

    website_content = result["platform_variants"]["website_listing"]["content"]
    assert website_content["title"]
    assert website_content["short_description"]
    assert website_content["long_description"]
    assert website_content.get("hashtags", []) == []


def test_unsupported_platform_returns_warning_error(sample_formatted_output):
    adapter = PlatformAdapter()
    result = adapter.adapt({"content_type": "property_description", "formatted_output": sample_formatted_output, "metadata": {}}, ["unsupported_platform"])

    assert result["success"] is False
    assert result["warnings"] or result["errors"]


def test_hashtags_are_removed_from_email(sample_formatted_output):
    adapter = PlatformAdapter()
    payload = dict(sample_formatted_output)
    payload["hashtags"] = ["#Mallorca", "#RealEstate"]
    result = adapter.adapt({"content_type": "property_description", "formatted_output": payload, "metadata": {}}, ["email"])

    assert result["platform_variants"]["email"]["content"].get("hashtags", []) == []


def test_website_listing_remains_factual(sample_formatted_output):
    adapter = PlatformAdapter()
    result = adapter.adapt({"content_type": "property_description", "formatted_output": sample_formatted_output, "metadata": {}}, ["website_listing"])

    website_content = result["platform_variants"]["website_listing"]["content"]
    assert "Request a viewing" in website_content["cta"]
    assert "Guarant" not in website_content["long_description"]
