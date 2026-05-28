"""Tests for the end-to-end generation pipeline."""

from __future__ import annotations

import json

from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig


def test_pipeline_validates_request(sample_generation_request):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=False))
    valid, reason = pipeline.validate_request(sample_generation_request)

    assert valid is True
    assert reason is None


def test_pipeline_rejects_unsupported_content_type(sample_generation_request):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=False))
    request = dict(sample_generation_request)
    request["content_type"] = "unsupported_content"
    valid, reason = pipeline.validate_request(request)

    assert valid is False
    assert "Unsupported content type" in reason


def test_pipeline_handles_missing_brand(sample_generation_request):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=False))
    request = dict(sample_generation_request)
    request["brand"] = ""
    valid, reason = pipeline.validate_request(request)

    assert valid is False
    assert "Missing required field: brand" in reason


def test_pipeline_builds_prompt_payload(sample_generation_request):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=False))
    context = pipeline.load_context(sample_generation_request["brand"])
    prompt = pipeline.build_prompt(sample_generation_request, context)

    assert prompt["prompt_payload"]
    assert prompt["prompt_payload"]["system_prompt"]
    assert prompt["prompt_payload"]["user_prompt"]


def test_pipeline_handles_mocked_openai_success(sample_generation_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(
        config=PipelineConfig(
            enable_live_generation=True,
            enable_output_formatting=True,
            enable_output_validation=True,
            enable_rendering=True,
            enable_platform_adaptation=True,
            enable_governance_validation=True,
            enable_campaign_composition=True,
            enable_asset_coordination=True,
        )
    )
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_generation_request)

    assert result["success"] is True
    assert result["parsed_output"]
    assert result["formatted_output"]
    assert result["adaptation_result"] is not None
    assert result["governance_result"] is not None
    assert result["campaign_result"] is not None
    assert result["asset_coordination_result"] is not None


def test_pipeline_handles_missing_api_key_gracefully(sample_generation_request):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=False))
    result = pipeline.generate(sample_generation_request)

    assert result["success"] is False
    assert "live generation disabled" in result["error"].lower() or "openai api key" in result["error"].lower()


def test_pipeline_returns_structured_result(sample_generation_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(
        config=PipelineConfig(
            enable_live_generation=True,
            enable_output_formatting=True,
            enable_output_validation=True,
            enable_rendering=True,
            enable_platform_adaptation=True,
            enable_governance_validation=True,
            enable_campaign_composition=True,
            enable_asset_coordination=True,
        )
    )
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_generation_request)

    for field in ("brand", "platform", "content_type", "prompt_payload", "parsed_output", "formatted_output", "metadata"):
        assert field in result


def test_pipeline_includes_parsed_output(sample_generation_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=True))
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_generation_request)

    assert result["parsed_output"]


def test_pipeline_includes_formatted_output_when_enabled(sample_generation_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=True, enable_output_formatting=True))
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_generation_request)

    assert result["formatted_output"]


def test_pipeline_includes_governance_result_when_enabled(sample_generation_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=True, enable_governance_validation=True))
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_generation_request)

    assert result["governance_result"] is not None


def test_pipeline_includes_adaptation_result_when_enabled(sample_generation_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=True, enable_platform_adaptation=True))
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_generation_request)

    assert result["adaptation_result"] is not None


def test_pipeline_includes_campaign_result_when_enabled(sample_generation_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=True, enable_campaign_composition=True))
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_generation_request)

    assert result["campaign_result"] is not None


def test_pipeline_includes_asset_coordination_result_when_enabled(sample_generation_request, sample_ai_response):
    pipeline = ContentGenerationPipeline(config=PipelineConfig(enable_live_generation=True, enable_campaign_composition=True, enable_asset_coordination=True))
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_generation_request)

    assert result["asset_coordination_result"] is not None
    assert result["asset_plan"] is not None
    assert result["asset_requirements"] is not None


def test_pipeline_includes_video_script_result_when_enabled(sample_video_script_request, sample_video_script_ai_response):
    pipeline = ContentGenerationPipeline(
        config=PipelineConfig(
            enable_live_generation=True,
            enable_output_formatting=True,
            enable_output_validation=True,
            enable_rendering=True,
            enable_platform_adaptation=True,
            enable_governance_validation=True,
            enable_campaign_composition=True,
            enable_asset_coordination=True,
            enable_video_script_engine=True,
            enable_storyboard_generation=True,
        )
    )
    pipeline._can_generate_live = lambda: True  # type: ignore[assignment]
    pipeline.generate_ai_response = lambda payload: sample_video_script_ai_response  # type: ignore[assignment]

    result = pipeline.generate(sample_video_script_request)

    assert result["video_script_result"] is not None
    assert result["video_type"] == "instagram_reel"
    assert result["video_duration"] == "30s"
    assert result["scene_sequence"]
    assert result["storyboard"]
    assert result["video_script_validation"] is not None
    assert result["asset_coordination_result"] is not None
    assert result["governance_result"] is not None
