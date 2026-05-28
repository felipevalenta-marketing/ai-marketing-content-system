"""Tests for reusable visual style presets."""

from __future__ import annotations

from src.media.visual_styles import DEFAULT_VISUAL_STYLE, get_visual_style, list_visual_styles


def test_visual_styles_include_expected_presets():
    styles = list_visual_styles()

    assert "mediterranean_lifestyle" in styles
    assert "premium_interior" in styles
    assert "natural_light_editorial" in styles


def test_get_visual_style_returns_fallback_for_unknown_style():
    style = get_visual_style("not_a_real_style")

    assert style["name"] == DEFAULT_VISUAL_STYLE
    assert style["lighting"]
    assert style["composition"]
