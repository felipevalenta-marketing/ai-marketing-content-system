"""Tests for the creative direction engine and pipeline integration."""

from __future__ import annotations

from argparse import Namespace

from src.cli.commands import handle_generate
from src.creative.creative_direction_engine import CreativeDirectionEngine
from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig


def test_creative_direction_engine_generates_structured_result(sample_creative_direction_request):
    engine = CreativeDirectionEngine()

    result = engine.generate_creative_direction(sample_creative_direction_request)

    assert result["success"] is True
    assert result["creative_direction_type"]
    assert result["visual_identity"]["name"]
    assert result["moodboard"]["rules"]
    assert result["color_palette"]["name"]
    assert result["platform_guidelines"]
    assert result["media_guidelines"]


def test_creative_direction_engine_uses_visual_identity_fallback():
    engine = CreativeDirectionEngine()
    request = {
        "brand": "wenzel_partner",
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "platforms": ["instagram"],
        "visual_style": "not_a_real_style",
        "creative_direction": "Calm Mediterranean property reveal.",
    }

    result = engine.generate_creative_direction(request)

    assert result["success"] is True
    assert result["visual_identity"]["name"]
    assert result["visual_identity"]["name"] != "not_a_real_style"


def test_creative_direction_pipeline_integration(sample_creative_direction_request):
    pipeline = ContentGenerationPipeline(
        config=PipelineConfig(
            enable_live_generation=False,
            enable_creative_direction_engine=True,
            enable_reporting=False,
        )
    )

    result = pipeline.generate(sample_creative_direction_request)

    assert result["success"] is True
    assert result["creative_direction_result"] is not None
    assert result["creative_direction_type"]
    assert result["visual_identity"]
    assert result["moodboard"]
    assert result["color_palette"]
    assert result["creative_validation"] is not None


def test_creative_direction_cli_dry_run(sample_creative_direction_request):
    args = Namespace(
        brand=sample_creative_direction_request["brand"],
        platform="instagram",
        content_type="creative_direction",
        audience=sample_creative_direction_request["audience"],
        location=sample_creative_direction_request["location"],
        property_type=sample_creative_direction_request["property_type"],
        objective=sample_creative_direction_request["objective"],
        campaign_type=sample_creative_direction_request["campaign_type"],
        visual_style=sample_creative_direction_request["visual_style"],
        creative_direction=sample_creative_direction_request["creative_direction"],
        extra_notes=sample_creative_direction_request["extra_notes"],
        dry_run=True,
        export=False,
        json=False,
        markdown=False,
        report=False,
        report_json=False,
        report_markdown=False,
        report_export=False,
    )

    result = handle_generate(args)

    assert result["success"] is True
    assert result["payload"]["creative_direction_result"]["success"] is True
