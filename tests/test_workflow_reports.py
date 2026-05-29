from __future__ import annotations

from pathlib import Path

from src.reports.markdown_exporter import MarkdownExporter
from src.reports.markdown_generator import MarkdownReportGenerator
from src.reports.markdown_validator import MarkdownValidator


def _workflow_payload() -> dict[str, object]:
    return {
        "brand": "wenzel_partner",
        "platform": "instagram",
        "campaign_type": "property_launch",
        "content_type": "instagram_post",
        "workflow_type": "full_campaign_package",
        "workflow_id": "wf-123",
        "workflow_status": "completed",
        "workflow_state": {
            "workflow_id": "wf-123",
            "workflow_type": "full_campaign_package",
            "status": "completed",
            "history": [
                {"timestamp": "2026-05-29T10:00:00+00:00", "state": "planned", "detail": "Plan created"},
                {"timestamp": "2026-05-29T10:01:00+00:00", "state": "running", "detail": "Execution started"},
            ],
            "step_outputs": {
                "step_01_load_context": {"status": "completed", "warnings": [], "errors": []},
                "step_02_build_report": {"status": "completed", "warnings": [], "errors": []},
            },
        },
        "workflow_state_history": [
            {"timestamp": "2026-05-29T10:00:00+00:00", "state": "planned", "detail": "Plan created"},
            {"timestamp": "2026-05-29T10:01:00+00:00", "state": "running", "detail": "Execution started"},
        ],
        "workflow_timeline": [
            {"timestamp": "2026-05-29T10:01:00+00:00", "state": "running", "detail": "Execution started"},
            {"timestamp": "2026-05-29T10:02:00+00:00", "state": "completed", "detail": "Workflow completed"},
        ],
        "workflow_status_transitions": [
            {"from": "planned", "to": "running", "reason": "Workflow started"},
            {"from": "running", "to": "completed", "reason": "All steps finished"},
        ],
        "token_summary": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "input_tokens": 240,
            "output_tokens": 120,
            "cached_input_tokens": 12,
            "total_tokens": 372,
            "estimated": False,
            "source": "provider_usage",
        },
        "cost_summary": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "currency": "USD",
            "input_cost": 0.01,
            "output_cost": 0.02,
            "cached_input_cost": 0.001,
            "generation_cost": 0.031,
            "workflow_cost": 0.031,
            "total_cost": 0.031,
            "estimated_cost": False,
            "pricing_found": True,
            "pricing_version": "local_default",
            "pricing_source": "configurable",
        },
        "storage_summary": {
            "storage_root": "data",
            "records_saved": 4,
            "stored_record_ids": ["wf-123", "state-123"],
            "markdown_saved": True,
            "persistence_status": "saved",
            "generated_artifacts": ["generation.json"],
            "report_exports": ["workflow.md"],
            "workflow_snapshots": ["state_snapshot.json"],
            "execution_archives": ["archive.json"],
            "warnings": ["Storage root is local only."],
        },
        "governance_result": {"status": "approved", "overall_score": 94, "warnings": [], "errors": []},
        "campaign_result": {"campaign_name": "property_launch", "campaign_type": "property_launch", "assets": ["image_prompt", "video_prompt", "social_post"]},
        "asset_coordination_result": {"asset_count": 3, "missing_assets": [], "generated_assets": ["image_prompt", "video_prompt", "social_post"]},
        "image_prompt_result": {
            "success": True,
            "image_type": "property_exterior",
            "visual_style": "mediterranean_lifestyle",
            "aspect_ratio": "4:5",
            "negative_prompt": "blurry, watermark",
        },
        "image_prompt_validation": {
            "valid": True,
            "warnings": [],
            "errors": [],
            "scores": {"realism": 92, "completeness": 90, "brand_fit": 95, "platform_fit": 91, "conciseness": 88},
        },
        "video_script_result": {
            "success": True,
            "video_type": "instagram_reel",
            "duration": "30s",
            "hook": "Rustic calm in Mallorca",
            "cta": "Contact our team to learn more.",
            "music_mood": "warm, premium, light acoustic",
            "storyboard": [
                {"frame_number": 1, "scene_number": 1, "shot_type": "wide", "visual_description": "Exterior at golden hour", "camera_direction": "slow push in", "lighting": "natural light", "motion": "gentle", "on_screen_text": "Mallorca living", "voiceover": "A calm, premium home in Mallorca."},
            ],
        },
        "video_script_validation": {
            "valid": True,
            "warnings": [],
            "errors": [],
            "scores": {"structure": 92, "pacing": 90, "brand_fit": 95, "platform_fit": 91, "factual_safety": 94},
        },
        "creative_direction_result": {
            "creative_direction_type": "campaign_visual_direction",
            "visual_identity": {"name": "mediterranean_luxury", "mood": "warm"},
            "moodboard": {"rules": ["warm_mediterranean_light"]},
            "color_palette": {"name": "mediterranean_neutrals"},
            "lighting_direction": "natural golden light",
            "camera_style": "editorial wide angle",
        },
    }


def test_markdown_report_generator_renders_workflow_snapshot_and_summary(tmp_path: Path) -> None:
    generator = MarkdownReportGenerator(output_root=tmp_path)
    payload = {
        **_workflow_payload(),
        "report_type": "workflow_report",
        "title": "Campaign Workflow Report",
        "export_markdown_report": True,
    }

    result = generator.generate_report(payload)

    assert result["success"] is True
    assert "## Workflow Snapshot" in result["markdown"]
    assert "## Workflow Timeline" in result["markdown"]
    assert "## Status Transitions" in result["markdown"]
    assert "## Token Usage" in result["markdown"]
    assert "## Cost Usage" in result["markdown"]
    assert "## Storage" in result["markdown"]
    assert result["report_index_path"]
    assert Path(result["export_path"]).exists()


def test_markdown_report_generator_supports_media_report_types() -> None:
    generator = MarkdownReportGenerator()
    media_base = {
        "brand": "wenzel_partner",
        "platform": "instagram",
        "campaign_type": "property_launch",
        "content_type": "instagram_post",
        "title": "Media Report",
    }

    image_report = generator.generate_report({**media_base, "image_prompt_result": _workflow_payload()["image_prompt_result"], "image_prompt_validation": _workflow_payload()["image_prompt_validation"], "report_type": "", "title": "Image Prompt Report"})
    video_report = generator.generate_report({**media_base, "video_script_result": _workflow_payload()["video_script_result"], "video_script_validation": _workflow_payload()["video_script_validation"], "report_type": "", "title": "Video Script Report"})
    visual_report = generator.generate_report({**media_base, "visual_identity": _workflow_payload()["creative_direction_result"]["visual_identity"], "color_palette": _workflow_payload()["creative_direction_result"]["color_palette"], "moodboard": _workflow_payload()["creative_direction_result"]["moodboard"], "report_type": "", "title": "Visual Style Report"})

    assert image_report["report_type"] == "image_prompt_report"
    assert video_report["report_type"] == "video_script_report"
    assert visual_report["report_type"] == "visual_style_report"


def test_markdown_validator_allows_workflow_snapshot_and_metrics() -> None:
    validator = MarkdownValidator()
    result = validator.validate(
        {
            "report_type": "workflow_report",
            "title": "Campaign Workflow Report",
            "markdown": "# Campaign Workflow Report\n\n## Workflow Snapshot\n| Field | Value |\n| --- | --- |\n| Workflow ID | wf-123 |\n\n## Token Usage\n| Metric | Value |\n| --- | --- |\n| Input Tokens | 240 |\n\n## Cost Usage\n| Metric | Value |\n| --- | --- |\n| Total Cost | 0.031000 |",
            "metadata": {"brand": "wenzel_partner", "workflow_id": "wf-123"},
            "export_path": "outputs/reports/markdown/wenzel_partner/workflow_report/campaign.md",
        }
    )

    assert result["valid"] is True


def test_markdown_report_generator_builds_executive_summary_content() -> None:
    generator = MarkdownReportGenerator()
    result = generator.generate_executive_summary(
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "campaign_type": "property_launch",
            "content_type": "instagram_post",
            "title": "Executive Summary",
            "summary": {
                "status": "completed",
                "primary_outcome": "Campaign package prepared",
                "approval_status": "approved_with_warnings",
                "next_steps": "Review the generated assets and prepare export.",
            },
            "workflow_result": {
                "workflow_id": "wf-123",
                "workflow_type": "full_campaign_package",
                "status": "completed",
            },
            "asset_result": {
                "generated_assets": ["image_prompt", "video_prompt", "social_post"],
                "warnings": ["Image prompt needs final review."],
                "errors": ["No critical errors."],
            },
            "token_summary": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "input_tokens": 240,
                "output_tokens": 120,
                "total_tokens": 360,
                "estimated": False,
                "source": "provider_usage",
            },
            "cost_summary": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "currency": "USD",
                "total_cost": 0.031,
                "estimated_cost": False,
                "pricing_found": True,
                "pricing_version": "local_default",
                "pricing_source": "configurable",
            },
        }
    )

    assert result["success"] is True
    assert "Generated Assets" in result["markdown"]
    assert "Key Warnings" in result["markdown"]
    assert "Critical Errors" in result["markdown"]
