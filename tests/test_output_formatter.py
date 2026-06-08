"""Tests for output formatting, validation, and rendering."""

from __future__ import annotations

from src.output.output_formatter import OutputFormatter
from src.output.output_renderer import OutputRenderer
from src.output.output_validator import OutputValidator


def test_instagram_post_output_contract():
    formatter = OutputFormatter()
    parsed = {
        "json": {
            "hook": "Discover Mallorca",
            "caption": "Calm living with practical connectivity.",
            "cta": "Request a viewing",
            "hashtags": ["#Mallorca", "#RealEstate"],
        },
        "content": "",
        "raw_content": "",
    }
    output = formatter.format_instagram_post(parsed)

    assert output["content_type"] == "instagram_post"
    assert output["hook"]
    assert output["caption"]
    assert isinstance(output["hashtags"], list)


def test_instagram_reel_output_contract():
    formatter = OutputFormatter()
    parsed = {
        "json": {
            "hook": "Explore Mallorca",
            "script": "A simple reel script.",
            "scene_direction": "Natural daylight over a rustic home.",
            "cta": "Discover more",
            "hashtags": ["#Mallorca"],
        },
        "content": "",
        "raw_content": "",
    }
    output = formatter.format_instagram_reel(parsed)

    assert output["content_type"] == "instagram_reel"
    assert output["script"]


def test_property_description_output_contract(sample_parsed_output):
    formatter = OutputFormatter()
    output = formatter.format_property_description(sample_parsed_output)

    assert output["content_type"] == "property_description"
    assert output["title"]
    assert output["description"]


def test_ad_copy_output_contract():
    formatter = OutputFormatter()
    parsed = {
        "json": {
            "headline": "Limited availability in Mallorca",
            "primary_text": "A calm, grounded home with real lifestyle appeal.",
            "description": "Targeted paid social copy.",
            "cta": "Learn more today",
        },
        "content": "",
        "raw_content": "",
    }
    output = formatter.format(parsed, "ad_copy")

    assert output["content_type"] == "ad_copy"
    assert output["headline"]
    assert output["primary_text"]


def test_image_prompt_output_contract():
    formatter = OutputFormatter()
    parsed = {
        "json": {
            "image_prompt": "Mediterranean natural light with a wide exterior shot.",
            "camera": "Wide exterior photography",
            "lighting": "Soft daylight",
            "style": "Premium but approachable",
            "negative_prompt": "No people, no text overlays",
        },
        "content": "",
        "raw_content": "",
    }
    output = formatter.format_image_prompt(parsed)

    assert output["image_prompt"]
    assert output["style"]
    assert output["camera"]


def test_video_prompt_output_contract():
    formatter = OutputFormatter()
    parsed = {
        "json": {
            "scene_description": "Tour the property exterior.",
            "camera_motion": "Slow push-in",
            "mood": "Calm",
            "sequence": ["Exterior", "Interior"],
            "voiceover_direction": "Warm and grounded",
        },
        "content": "",
        "raw_content": "",
    }
    output = formatter.format_video_prompt(parsed)

    assert output["scene_description"]
    assert isinstance(output["sequence"], list)


def test_video_script_output_contract():
    formatter = OutputFormatter()
    parsed = {
        "json": {
            "hook": "A calm look at a Mallorca home.",
            "scene_1": "Exterior reveal with clean architectural framing.",
            "scene_2": "Interior sweep with natural light.",
            "scene_3": "Closing shot with location and CTA.",
            "voiceover": "A calm, premium property story.",
            "cta": "Send us a message to learn more.",
        },
        "content": "",
        "raw_content": "",
    }
    output = formatter.format_video_script(parsed)

    assert output["hook"]
    assert output["scene_1"]
    assert output["scene_2"]
    assert output["scene_3"]
    assert output["voiceover"]
    assert output["cta"]


def test_missing_optional_fields_are_safely_filled():
    formatter = OutputFormatter()
    output = formatter.format({"json": {"title": "Only title"}, "content": "", "raw_content": ""}, "property_description")

    assert "description" in output
    assert isinstance(output["highlights"], list)


def test_malformed_parsed_output_returns_warnings():
    formatter = OutputFormatter()
    output = formatter.format({"content": "Hook: Hello\nCTA: Request a viewing", "raw_content": "Hook: Hello"}, "instagram_post")

    assert output["formatting_warnings"]


def test_validator_catches_missing_required_fields():
    validator = OutputValidator()
    validation = validator.validate({"title": "", "description": "", "highlights": [], "cta": ""}, "property_description")

    assert not validation["valid"]
    assert validation["errors"]


def test_renderer_produces_markdown():
    renderer = OutputRenderer()
    output = {
        "title": "Rustic home",
        "description": "Long text",
        "highlights": ["Modern interiors"],
        "cta": "Request a viewing",
        "metadata": {"brand": "wenzel_partner"},
    }
    markdown = renderer.render_markdown(output, "property_description")

    assert "# Property Description" in markdown
    assert "## Metadata" in markdown


def test_renderer_produces_plain_text():
    renderer = OutputRenderer()
    output = {
        "title": "Rustic home",
        "description": "Long text",
        "highlights": ["Modern interiors"],
        "cta": "Request a viewing",
    }
    text = renderer.render_text(output, "property_description")

    assert "Rustic home" in text


def test_renderer_produces_json_ready_dict():
    renderer = OutputRenderer()
    data = renderer.render_json({"title": "Rustic home", "highlights": ["Modern interiors"]})

    assert isinstance(data, dict)
    assert data["title"] == "Rustic home"
