"""Tests for creative moodboard rules."""

from __future__ import annotations

from src.creative.moodboard_rules import list_moodboard_rules, resolve_moodboard_rules


def test_moodboard_rules_catalog_contains_expected_rules():
    rules = list_moodboard_rules()

    assert "warm_mediterranean_light" in rules
    assert "grounded_luxury" in rules


def test_moodboard_rules_resolve_for_property_launch():
    rules = resolve_moodboard_rules("property_launch", "instagram", asset_types=["image_prompt"])

    assert rules
    assert all("name" in rule for rule in rules)
