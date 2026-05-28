"""Tests for scene template library."""

from __future__ import annotations

from src.media.scene_templates import get_scene_template, list_scene_templates, resolve_scene_template
from src.media.storyboard_rules import resolve_storyboard_rules


def test_scene_template_listing():
    templates = list_scene_templates()

    assert "property_launch" in templates
    assert "brand_story_video" in templates


def test_get_scene_template_returns_copy():
    template = get_scene_template("property_launch")

    assert template["name"] == "property_launch"
    template["name"] = "changed"
    assert get_scene_template("property_launch")["name"] == "property_launch"


def test_resolve_scene_template_from_request(sample_video_script_request):
    template = resolve_scene_template(sample_video_script_request)

    assert template["scene_count"] >= 5
    assert template["cta_position"] == "final_scene"


def test_storyboard_rule_resolution(sample_video_script_request):
    rules = resolve_storyboard_rules(sample_video_script_request["video_type"], sample_video_script_request["platform"])

    assert rules
    assert all("rule_fragment" in rule for rule in rules)
