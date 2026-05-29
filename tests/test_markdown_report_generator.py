from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from src.cli.cli_app import build_parser
from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig
from src.reports.markdown_generator import MarkdownReportGenerator


def _sample_base_payload() -> dict[str, object]:
    return {
        "brand": "wenzel_partner",
        "platform": "instagram",
        "campaign_type": "property_launch",
        "content_type": "instagram_post",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "visual_style": "mediterranean_lifestyle",
        "creative_direction": "Rustic exterior with modern comfort inside, close to Manacor and beaches.",
        "token_summary": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "input_tokens": 100,
            "output_tokens": 50,
            "total_tokens": 150,
            "estimated": False,
            "source": "provider_usage",
        },
        "cost_summary": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "currency": "USD",
            "input_cost": 0.01,
            "output_cost": 0.02,
            "cached_input_cost": 0.0,
            "total_cost": 0.03,
            "estimated_cost": True,
            "pricing_found": False,
            "pricing_version": "local_default",
            "pricing_source": "configurable",
        },
        "storage_summary": {
            "storage_root": "data",
            "records_saved": 2,
            "stored_record_ids": ["one", "two"],
            "markdown_saved": True,
            "persistence_status": "saved",
        },
        "warnings": [],
        "errors": [],
        "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
    }


def test_markdown_report_generator_creates_workflow_report(sample_workflow_request: dict) -> None:
    generator = MarkdownReportGenerator()
    payload = {
        **_sample_base_payload(),
        "report_type": "workflow_report",
        "title": "Campaign Workflow Report",
        "workflow_result": {
            "workflow_id": "wf-1",
            "workflow_type": "full_campaign_package",
            "status": "completed",
            "summary": {"step_count": 2, "completed_steps": 2, "failed_steps": 0, "skipped_steps": 0, "duration_seconds": 1.5},
            "steps": [
                {"step_id": "step_01", "step_type": "load_context", "name": "Load Context", "status": "completed"},
                {"step_id": "step_02", "step_type": "build_report", "name": "Build Report", "status": "completed"},
            ],
        },
        "campaign_result": {"campaign_name": "sample_campaign", "campaign_type": "property_launch", "strategy": {"cta_strategy": "trust-first"}},
        "asset_coordination_result": {"asset_count": 2, "missing_assets": []},
        "governance_result": {"status": "approved", "overall_score": 92, "warnings": [], "errors": []},
        "formatted_output": {"hook": "Rustic calm in Mallorca", "caption": "A premium but approachable Mallorca home.", "cta": "Contact our team to learn more.", "hashtags": ["#Mallorca"]},
    }

    result = generator.generate_report(payload)

    assert result["success"] is True
    assert result["report_type"] == "workflow_report"
    assert result["markdown"].startswith("# Campaign Workflow Report")
    assert any(section["section_id"] == "workflow_summary" for section in result["sections"])


def test_markdown_report_generator_supports_generation_and_campaign_reports() -> None:
    generator = MarkdownReportGenerator()
    base = _sample_base_payload()

    generation = generator.generate_generation_report({**base, "title": "Generation Report", "formatted_output": {"hook": "Hook", "caption": "Caption", "cta": "Contact our team to learn more.", "hashtags": ["#Mallorca"]}})
    campaign = generator.generate_campaign_report({**base, "title": "Campaign Report", "campaign_result": {"campaign_name": "sample_campaign", "campaign_type": "property_launch", "strategy": {"cta_strategy": "trust-first"}}})
    executive = generator.generate_executive_summary({**base, "title": "Executive Summary", "workflow_result": {"workflow_id": "wf-1", "workflow_type": "full_campaign_package", "status": "completed"}})

    assert generation["success"] is True
    assert campaign["success"] is True
    assert executive["success"] is True
    assert "Generation Report" in generation["markdown"]
    assert "Campaign Report" in campaign["markdown"]
    assert "Executive Summary" in executive["markdown"]


def test_markdown_report_generator_handles_unsupported_type() -> None:
    generator = MarkdownReportGenerator()
    result = generator.generate_report({**_sample_base_payload(), "report_type": "unsupported_type", "title": "Fallback Report"})

    assert result["success"] is True
    assert any("unsupported report_type" in warning.lower() for warning in result["warnings"])
    assert result["report_type"] in {"executive_summary", "workflow_report", "campaign_report", "generation_report", "asset_report", "governance_report", "tracking_report", "cost_report", "storage_report", "creative_direction_report", "media_report"}


def test_markdown_report_generator_exports_markdown(tmp_path: Path) -> None:
    generator = MarkdownReportGenerator(output_root=tmp_path)
    payload = {
        **_sample_base_payload(),
        "report_type": "workflow_report",
        "title": "Workflow Report",
        "export_markdown_report": True,
        "workflow_result": {"workflow_id": "wf-1", "workflow_type": "full_campaign_package", "status": "completed"},
    }

    result = generator.generate_report(payload)

    assert result["success"] is True
    assert result["export_path"]
    assert Path(result["export_path"]).exists()


def test_markdown_report_generator_pipeline_integration() -> None:
    config = PipelineConfig(enable_live_generation=False, enable_reporting=True, enable_markdown_reports=True)
    pipeline = ContentGenerationPipeline(config=config)
    result = pipeline.generate(
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "objective": "generate_leads",
            "audience": "relocation_clients",
            "location": "sant_llorenc_des_cardassar",
            "property_type": "rustic_home",
            "report": True,
            "markdown": True,
            "dry_run": True,
        }
    )

    assert result.get("markdown_report", {}).get("markdown")
    assert result.get("markdown_report", {}).get("report_type") == "execution_report" or result.get("markdown_report", {}).get("report_type") == "workflow_report"


def test_markdown_report_generator_cli_flags_parse() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "generate",
            "--brand",
            "wenzel_partner",
            "--platform",
            "instagram",
            "--content-type",
            "instagram_post",
            "--objective",
            "generate_leads",
            "--report",
            "--markdown",
            "--report-type",
            "workflow_report",
            "--export-markdown-report",
        ]
    )

    assert args.markdown is True
    assert args.export_markdown_report is True
    assert args.report_type == "workflow_report"
