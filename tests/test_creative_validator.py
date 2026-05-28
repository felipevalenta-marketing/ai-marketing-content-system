"""Tests for creative direction validation."""

from __future__ import annotations

from src.creative.creative_direction_engine import CreativeDirectionEngine
from src.creative.creative_validator import CreativeDirectionValidator


def test_creative_validator_approves_safe_direction(sample_creative_direction_request):
    engine = CreativeDirectionEngine()
    validator = CreativeDirectionValidator()
    creative_result = engine.generate_creative_direction(sample_creative_direction_request)

    validation = validator.validate(creative_result)

    assert validation["scores"]["brand_fit"] >= 0
    assert validation["scores"]["visual_consistency"] >= 0
    assert validation["scores"]["platform_fit"] >= 0
    assert validation["scores"]["realism"] >= 0
    assert validation["scores"]["completeness"] >= 0
    assert validation["valid"] is True


def test_creative_validator_flags_fake_luxury():
    validator = CreativeDirectionValidator()

    validation = validator.validate(
        {
            "creative_direction_type": "campaign_visual_direction",
            "brand": "wenzel_partner",
            "campaign_type": "property_launch",
            "visual_identity": {"name": "mediterranean_luxury", "mood": "premium"},
            "moodboard": {"rules": [{"name": "warm_mediterranean_light"}]},
            "color_palette": {"name": "mediterranean_neutrals", "primary_colors": ["warm white"]},
            "lighting_direction": "Natural daylight",
            "camera_style": "Steady editorial framing",
            "composition_rules": [{"name": "rule"}],
            "platform_guidelines": {"instagram": {"tone": "warm"}},
            "media_guidelines": {"image_prompts": {}, "video_scripts": {}},
            "creative_direction": "Fake luxury with impossible architecture and fake view",
            "metadata": {},
        }
    )

    assert validation["errors"]
