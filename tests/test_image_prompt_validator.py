"""Tests for image prompt validation."""

from __future__ import annotations

from src.media.image_prompt_validator import ImagePromptValidator


def test_image_prompt_validator_approves_complete_prompt():
    validator = ImagePromptValidator()
    result = validator.validate(
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "image_prompt",
            "image_type": "property_exterior",
            "prompt": "Create a premium realistic architectural photograph with natural light and balanced composition.",
            "negative_prompt": "blurry, low quality",
            "visual_style": "mediterranean_lifestyle",
            "lighting_style": "natural daylight",
            "composition_style": "balanced editorial framing",
            "camera_direction": "Wide-angle exterior photography",
            "aspect_ratio": "4:5",
        }
    )

    assert result["valid"] is True
    assert result["scores"]["realism"] > 0


def test_image_prompt_validator_rejects_unsupported_aspect_ratio():
    validator = ImagePromptValidator()
    result = validator.validate(
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "image_prompt",
            "image_type": "property_exterior",
            "prompt": "Create a realistic property photo.",
            "negative_prompt": "blurry",
            "visual_style": "mediterranean_lifestyle",
            "lighting_style": "natural daylight",
            "composition_style": "balanced framing",
            "camera_direction": "Wide-angle exterior photography",
            "aspect_ratio": "2:1",
        }
    )

    assert result["valid"] is False
    assert any("Unsupported aspect ratio" in error for error in result["errors"])


def test_image_prompt_validator_flags_forbidden_claims():
    validator = ImagePromptValidator()
    result = validator.validate(
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "image_prompt",
            "image_type": "property_exterior",
            "prompt": "Fake luxury guaranteed ROI with impossible architecture.",
            "negative_prompt": "blurry",
            "visual_style": "mediterranean_lifestyle",
            "lighting_style": "natural daylight",
            "composition_style": "balanced framing",
            "camera_direction": "Wide-angle exterior photography",
            "aspect_ratio": "4:5",
        }
    )

    assert result["valid"] is False
    assert result["errors"]
