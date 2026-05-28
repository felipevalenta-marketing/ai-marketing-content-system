"""Tests for the local storage manager."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.cli.cli_app import build_parser
from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig
from src.storage.storage_manager import StorageManager


def test_storage_manager_save_load_list_and_duplicate_handling(tmp_path: Path):
    manager = StorageManager(storage_root=tmp_path)
    record = {
        "record_type": "generation",
        "record_id": "generation_demo_1",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "instagram_post",
        "campaign_type": "property_launch",
        "execution_id": "exec-1",
        "source_module": "pipeline",
        "payload": {"title": "Sample", "content": "Calm Mallorca living."},
        "metadata": {"brand": "wenzel_partner"},
        "warnings": [],
        "errors": [],
    }

    saved = manager.save_record(record)
    assert saved["success"] is True
    assert saved["record_id"] == "generation_demo_1"

    loaded = manager.load_record("generation", "generation_demo_1")
    assert loaded["success"] is True
    assert loaded["record"]["payload"]["title"] == "Sample"

    listed = manager.list_records("generation")
    assert len(listed) == 1
    assert listed[0]["record_id"] == "generation_demo_1"

    duplicate = manager.save_record(record)
    assert duplicate["success"] is False
    assert any("File already exists" in error for error in duplicate["errors"])


def test_storage_manager_build_snapshot(tmp_path: Path):
    manager = StorageManager(storage_root=tmp_path)
    snapshot = manager.build_snapshot(
        [
            {"record_id": "one", "record_type": "generation", "payload": {"a": 1}},
            {"record_id": "two", "record_type": "report", "payload": {"b": 2}},
        ]
    )
    assert snapshot["snapshot_id"]
    assert snapshot["metadata"]["record_count"] == 2


def test_pipeline_persistence_integration(tmp_path: Path, sample_generation_request):
    pipeline = ContentGenerationPipeline(
        config=replace(
            PipelineConfig(),
            enable_persistence=True,
            persist_generations=True,
            persist_reports=True,
            persist_tracking=True,
            persist_markdown=True,
            storage_root=str(tmp_path / "data"),
            storage_overwrite=False,
        )
    )

    result = {
        "success": True,
        "brand": sample_generation_request["brand"],
        "platform": sample_generation_request["platform"],
        "content_type": sample_generation_request["content_type"],
        "campaign_type": "property_launch",
        "metadata": {
            "brand": sample_generation_request["brand"],
            "platform": sample_generation_request["platform"],
            "content_type": sample_generation_request["content_type"],
            "execution": {"started_at": "2026-01-01T00:00:00+00:00", "stages": {}},
            "context_summary": {"brand": "wenzel_partner", "notes": "safe context blob"},
        },
        "token_usage": {
            "success": True,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "estimated": False,
            "source": "provider_usage",
            "execution_id": "exec-1",
            "module": "instagram_post",
            "operation": "generation",
            "campaign_id": "property_launch",
            "asset_type": "instagram_post",
            "metadata": {},
            "warnings": [],
            "errors": [],
        },
        "cost_usage": {
            "success": True,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "currency": "USD",
            "input_tokens": 10,
            "output_tokens": 5,
            "cached_input_tokens": 0,
            "total_tokens": 15,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "cached_input_cost": 0.0,
            "total_cost": 0.0,
            "estimated_tokens": False,
            "estimated_cost": True,
            "pricing_found": False,
            "pricing_version": "local_default",
            "pricing_source": "configurable",
            "execution_id": "exec-1",
            "module": "instagram_post",
            "operation": "generation",
            "campaign_id": "property_launch",
            "asset_type": "instagram_post",
            "metadata": {},
            "warnings": ["Pricing not found for provider/model."],
            "errors": [],
        },
        "campaign_result": {
            "brand": sample_generation_request["brand"],
            "platform": sample_generation_request["platform"],
            "campaign_type": "property_launch",
            "campaign_name": "launch_demo",
            "metadata": {},
            "warnings": [],
            "errors": [],
        },
        "asset_coordination_result": {
            "brand": sample_generation_request["brand"],
            "campaign_type": "property_launch",
            "asset_plan": {"required_assets": ["image_prompt"]},
            "metadata": {},
            "warnings": [],
            "errors": [],
        },
        "creative_direction_result": {
            "brand": sample_generation_request["brand"],
            "campaign_type": "property_launch",
            "creative_direction_type": "campaign_visual_direction",
            "visual_identity": {"name": "mediterranean_luxury"},
            "moodboard": {"rules": ["warm_mediterranean_light"]},
            "color_palette": {"name": "mediterranean_neutrals"},
            "platform_guidelines": {},
            "media_guidelines": {},
            "metadata": {},
            "warnings": [],
            "errors": [],
        },
        "image_prompt_result": {
            "brand": sample_generation_request["brand"],
            "platform": sample_generation_request["platform"],
            "content_type": "image_prompt",
            "image_type": "property_exterior",
            "prompt": "Premium Mallorca exterior in natural light.",
            "negative_prompt": "blurry, low quality",
            "visual_style": "mediterranean_lifestyle",
            "lighting_style": "natural daylight",
            "composition_style": "rule of thirds",
            "camera_direction": "wide-angle",
            "aspect_ratio": "4:5",
            "metadata": {},
            "warnings": [],
            "errors": [],
        },
        "video_script_result": {
            "brand": sample_generation_request["brand"],
            "platform": sample_generation_request["platform"],
            "content_type": "video_script",
            "video_type": "instagram_reel",
            "duration": "30s",
            "hook": "Discover calm Mallorca living.",
            "script": "Show the exterior, then the interior comfort, then the location payoff.",
            "voiceover": "Discover calm Mallorca living.",
            "cta": "Contact our team to learn more.",
            "music_mood": "warm and elegant",
            "scene_sequence": [],
            "storyboard": [],
            "camera_direction": {},
            "metadata": {},
            "warnings": [],
            "errors": [],
        },
        "consolidated_report": {
            "title": "Consolidated report",
            "summary": {},
            "metrics": {},
            "warnings": [],
            "errors": [],
            "metadata": {},
            "sections": {},
        },
        "execution_report": {
            "title": "Execution report",
            "summary": {},
            "metrics": {},
            "warnings": [],
            "errors": [],
            "metadata": {},
            "sections": {},
        },
        "warnings": [],
        "errors": [],
    }

    persisted = pipeline._attach_persistence(result, request=sample_generation_request, context={"summary": {}})
    assert persisted["persistence_result"]["success"] is True
    assert persisted["persistence_result"]["records_saved"] >= 1
    assert persisted["storage_paths"]
    assert persisted["stored_record_ids"]
    assert (tmp_path / "data" / "generations").exists()
    assert (tmp_path / "data" / "indexes").exists()
    assert persisted["execution_report"]["sections"]["persistence"]["records_saved"] >= 1


def test_storage_manager_prunes_nested_context_blobs(tmp_path: Path):
    manager = StorageManager(storage_root=tmp_path)
    record = {
        "record_type": "generation",
        "record_id": "generation_context_blob",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "instagram_post",
        "campaign_type": "property_launch",
        "execution_id": "exec-ctx",
        "source_module": "pipeline",
        "payload": {
            "brand": "wenzel_partner",
            "metadata": {
                "context_summary": "this is a long context blob with the word secret in it",
                "reporting": {"persistence": {"records_saved": 1}},
            },
            "cost": {
                "cost_usage": {
                    "metadata": {
                        "context_summary": "another secret context blob",
                    }
                }
            },
        },
        "metadata": {
            "brand": "wenzel_partner",
            "context_summary": "top-level context blob",
            "reporting": {"persistence": {"records_saved": 1}},
        },
        "warnings": [],
        "errors": [],
    }

    saved = manager.save_record(record)
    assert saved["success"] is True
    loaded = manager.load_record("generation", "generation_context_blob")
    assert loaded["success"] is True
    assert "context_summary" not in loaded["record"]["payload"]["metadata"]
    assert "context_summary" not in loaded["record"]["payload"]["cost"]["cost_usage"]["metadata"]


def test_cli_parser_accepts_persistence_flags():
    parser = build_parser()
    args = parser.parse_args(["generate", "--persist", "--persist-markdown", "--storage-root", "tmp-data"])
    assert args.persist is True
    assert args.persist_markdown is True
    assert args.storage_root == "tmp-data"
