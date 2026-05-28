"""Tests for creative color palettes."""

from __future__ import annotations

from src.creative.color_palette import get_color_palette, list_color_palettes


def test_color_palette_catalog_contains_expected_palettes():
    palettes = list_color_palettes()

    assert "mediterranean_neutrals" in palettes
    assert "rustic_earth_tones" in palettes


def test_color_palette_returns_descriptive_profile():
    palette = get_color_palette("rustic_earth_tones")

    assert palette["name"] == "rustic_earth_tones"
    assert palette["primary_colors"]
    assert palette["usage_notes"]
