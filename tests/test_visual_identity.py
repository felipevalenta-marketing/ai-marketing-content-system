"""Tests for creative visual identity profiles."""

from __future__ import annotations

from src.creative.visual_identity import DEFAULT_VISUAL_IDENTITY, get_visual_identity, list_visual_identities


def test_visual_identity_catalog_contains_expected_profiles():
    profiles = list_visual_identities()

    assert "mediterranean_luxury" in profiles
    assert "relocation_warmth" in profiles


def test_visual_identity_falls_back_safely():
    profile = get_visual_identity("does_not_exist")

    assert profile["name"] == DEFAULT_VISUAL_IDENTITY
    assert profile["mood"]
    assert profile["lighting"]
