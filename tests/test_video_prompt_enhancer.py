"""Tests for video prompt enhancement."""

from __future__ import annotations

from src.media.video_prompt_enhancer import VideoPromptEnhancer


def test_script_enhancement(sample_video_script_request):
    enhancer = VideoPromptEnhancer()
    script = "Hook line.\nHook line.\nLimited time only.\nAct now.\nMore details here."
    enhanced = enhancer.enhance_script(script, sample_video_script_request)

    assert "Limited time only" not in enhanced
    assert "Act now" not in enhanced
    assert enhanced


def test_duplicate_phrase_removal():
    enhancer = VideoPromptEnhancer()
    script = "Line one.\nLine one.\nLine two."

    assert enhancer.remove_duplicate_phrases(script).count("Line one.") == 1


def test_pacing_enforcement():
    enhancer = VideoPromptEnhancer()
    script = "\n".join([f"Line {index}" for index in range(10)])

    assert len(enhancer.enforce_pacing(script, "15s").splitlines()) <= 8


def test_brand_safety_enforcement():
    enhancer = VideoPromptEnhancer()
    script = "Guaranteed ROI and limited time only."

    assert "Guaranteed ROI" not in enhancer.enforce_brand_safety(script)


def test_voiceover_length_optimization():
    enhancer = VideoPromptEnhancer()
    script = " ".join(["word"] * 120)

    assert len(enhancer.optimize_voiceover_length(script, "30s").split()) <= 68
