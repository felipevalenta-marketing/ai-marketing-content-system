"""Tests for the advanced image prompt generation engine."""

from __future__ import annotations

import json

from src.cli.cli_app import build_parser
from src.media.image_prompt_engine import ImagePromptEngine
from src.media.visual_styles import DEFAULT_VISUAL_STYLE
from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig


def test_image_prompt_engine_generates_structured_prompt(sample_image_prompt_request):
    engine = ImagePromptEngine()
    result = engine.generate_image_prompt(sample_image_prompt_request)

    assert result["success"] is True
    assert result["prompt"]
    assert result["negative_prompt"]
    assert result["visual_style"] == "mediterranean_lifestyle"
    assert result["aspect_ratio"] == "4:5"
    assert result["cinematic_rules_applied"]
    assert result["validation"]["valid"] is True


def test_image_prompt_engine_uses_supported_style_and_fallback():
    engine = ImagePromptEngine()
    request = {
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "image_prompt",
        "image_type": "property_exterior",
        "aspect_ratio": "4:5",
        "creative_direction": "Rustic exterior with modern comfort inside.",
        "visual_style": "not_real_style",
    }
    result = engine.generate_image_prompt(request)

    assert result["visual_style"] == DEFAULT_VISUAL_STYLE
    assert result["warnings"]


def test_image_prompt_engine_handles_unsupported_aspect_ratio_gracefully():
    engine = ImagePromptEngine()
    request = {
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "image_prompt",
        "image_type": "property_exterior",
        "aspect_ratio": "2:1",
        "creative_direction": "Rustic exterior with modern comfort inside.",
        "visual_style": "mediterranean_lifestyle",
    }
    valid, reason = engine.validate_request(request)

    assert valid is True
    assert reason is not None
    assert "aspect ratio" in reason.lower()


def test_image_prompt_pipeline_integration(sample_image_prompt_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(
        config=PipelineConfig(
            enable_live_generation=True,
            enable_output_formatting=True,
            enable_output_validation=True,
            enable_rendering=True,
            enable_governance_validation=True,
            enable_campaign_composition=True,
            enable_asset_coordination=True,
            enable_image_prompt_engine=True,
            enable_cinematic_enhancement=True,
            enable_negative_prompts=True,
        )
    )
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: {
        "success": True,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "content": json.dumps(
            {
                "visual_direction": "Premium but realistic exterior photo of a rustic Mallorca home.",
                "subject": "Rustic home",
                "composition": "Wide exterior framing",
                "lighting": "Natural daylight",
                "style": "Mediterranean lifestyle",
                "negative_prompt": "blurry, low quality",
            }
        ),
        "raw_response": {"content": "mocked"},
        "metadata": {"provider": "openai", "model": "gpt-4o-mini", "warnings": []},
        "error": None,
    }  # type: ignore[assignment]

    result = pipeline.generate(sample_image_prompt_request)

    assert result["success"] is True
    assert result["image_prompt_result"]
    assert result["enhanced_image_prompt"]
    assert result["negative_prompt"]
    assert result["visual_style"]
    assert result["image_prompt_validation"]
    assert result["asset_plan"].get("generation_readiness", {}).get("image_prompt_ready", {}).get("ready") is True


def test_cli_generate_parser_accepts_image_prompt_flags():
    parser = build_parser()
    args = parser.parse_args(
        [
            "generate",
            "--brand",
            "wenzel_partner",
            "--platform",
            "instagram",
            "--content-type",
            "image_prompt",
            "--image-type",
            "property_exterior",
            "--aspect-ratio",
            "4:5",
            "--visual-style",
            "mediterranean_lifestyle",
            "--objective",
            "generate_leads",
            "--audience",
            "relocation_clients",
        ]
    )

    assert args.image_type == "property_exterior"
    assert args.aspect_ratio == "4:5"
    assert args.visual_style == "mediterranean_lifestyle"
