"""Tests for video script generation."""

from __future__ import annotations

from src.media.video_script_engine import VideoScriptEngine


def test_video_script_generation(sample_video_script_request):
    engine = VideoScriptEngine()
    result = engine.generate_video_script(sample_video_script_request)

    assert result["success"] is True
    assert result["video_type"] == "instagram_reel"
    assert result["duration"] == "30s"
    assert result["hook"]
    assert result["script"]
    assert result["voiceover"]
    assert result["cta"]
    assert isinstance(result["scene_sequence"], list)
    assert isinstance(result["storyboard"], list)
    assert result["camera_direction"]


def test_scene_template_selection(sample_video_script_request):
    engine = VideoScriptEngine()
    template = engine.select_scene_template(sample_video_script_request)

    assert template["name"] in {"property_launch", "instagram_reel"}
    assert template["scene_count"] >= 5
    assert template["scene_purposes"]


def test_storyboard_generation(sample_video_script_request):
    engine = VideoScriptEngine()
    template = engine.select_scene_template(sample_video_script_request)
    scenes = engine.build_scene_sequence(sample_video_script_request, template)
    storyboard = engine.build_storyboard(sample_video_script_request, scenes)

    assert len(storyboard) == len(scenes)
    assert storyboard[0]["scene_number"] == 1
    assert storyboard[0]["visual_description"]


def test_voiceover_building(sample_video_script_request):
    engine = VideoScriptEngine()
    template = engine.select_scene_template(sample_video_script_request)
    scenes = engine.build_scene_sequence(sample_video_script_request, template)
    voiceover = engine.build_voiceover(sample_video_script_request, scenes)

    assert voiceover
    assert isinstance(voiceover, str)


def test_cta_generation(sample_video_script_request):
    engine = VideoScriptEngine()

    assert engine.build_cta(sample_video_script_request)


def test_unsupported_duration_handling(sample_video_script_request):
    engine = VideoScriptEngine()
    request = dict(sample_video_script_request)
    request["duration"] = "12s"
    valid, reason = engine.validate_request(request)

    assert valid is True
    assert "unsupported duration" in (reason or "").lower()
