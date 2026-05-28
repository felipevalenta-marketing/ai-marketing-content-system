"""Tests for the image prompt enhancer."""

from __future__ import annotations

from src.media.prompt_enhancer import PromptEnhancer


def test_prompt_enhancer_removes_duplicates_and_keeps_prompt_compact():
    enhancer = PromptEnhancer()
    prompt = "Premium property. Premium property. Natural light. Natural light."

    cleaned = enhancer.remove_duplicate_phrases(prompt)

    assert cleaned.count("Premium property") == 1
    assert cleaned.count("Natural light") == 1


def test_prompt_enhancer_enforces_realism_and_brand_safety():
    enhancer = PromptEnhancer()
    prompt = "Fake luxury with guaranteed ROI and unrealistic lighting."

    enforced = enhancer.enforce_brand_safety(enhancer.enforce_realism(prompt))

    assert "guaranteed roi" not in enforced.lower()
    assert "fake luxury" not in enforced.lower()
    assert "unrealistic lighting" not in enforced.lower()


def test_prompt_enhancer_optimizes_length():
    enhancer = PromptEnhancer()
    prompt = "Sentence one. " * 200

    optimized = enhancer.optimize_prompt_length(prompt)

    assert len(optimized) <= 900
