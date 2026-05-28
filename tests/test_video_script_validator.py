"""Tests for video script validation."""

from __future__ import annotations

from src.media.video_script_engine import VideoScriptEngine
from src.media.video_script_validator import VideoScriptValidator


def test_video_script_validator_scores(sample_video_script_request):
    engine = VideoScriptEngine()
    result = engine.generate_video_script(sample_video_script_request)
    validation = result["validation"]

    assert validation["valid"] is True
    for key in ("structure", "pacing", "brand_fit", "platform_fit", "factual_safety"):
        assert key in validation["scores"]


def test_video_script_validator_flags_missing_cta(sample_video_script_request):
    validator = VideoScriptValidator()
    payload = {
        "brand": sample_video_script_request["brand"],
        "platform": sample_video_script_request["platform"],
        "content_type": "video_script",
        "video_type": sample_video_script_request["video_type"],
        "duration": sample_video_script_request["duration"],
        "hook": "Hook",
        "script": "A script with no CTA.",
        "voiceover": "A script with no CTA.",
        "cta": "",
        "music_mood": "calm",
        "scene_sequence": [{"scene_number": 1}],
        "storyboard": [{"frame_number": 1}],
    }
    validation = validator.validate(payload)

    assert validation["warnings"]


def test_unsupported_duration_returns_error(sample_video_script_request):
    validator = VideoScriptValidator()
    payload = {
        "brand": sample_video_script_request["brand"],
        "platform": sample_video_script_request["platform"],
        "content_type": "video_script",
        "video_type": sample_video_script_request["video_type"],
        "duration": "12s",
        "hook": "Hook",
        "script": "A script.",
        "voiceover": "A script.",
        "cta": "Contact our team to learn more.",
        "music_mood": "calm",
        "scene_sequence": [{"scene_number": 1}],
        "storyboard": [{"frame_number": 1}],
    }
    validation = validator.validate(payload)

    assert any("Unsupported duration" in error for error in validation["errors"])
