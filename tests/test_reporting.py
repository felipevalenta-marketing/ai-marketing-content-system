from __future__ import annotations

from pathlib import Path

from src.reporting.reporting_engine import ReportingEngine
from src.reporting.report_builder import ReportBuilder
from src.reporting.report_exporter import ReportExporter
from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig


def test_reporting_engine_builds_consolidated_report(sample_generation_request: dict, sample_governance_payload: dict) -> None:
    engine = ReportingEngine()
    payload = {
        "success": True,
        "brand": sample_generation_request["brand"],
        "platform": sample_generation_request["platform"],
        "content_type": sample_generation_request["content_type"],
        "metadata": {
            "brand": sample_generation_request["brand"],
            "platform": sample_generation_request["platform"],
            "content_type": sample_generation_request["content_type"],
            "objective": sample_generation_request["objective"],
            "audience": sample_generation_request["audience"],
            "execution": {
                "started_at": "2026-01-01T00:00:00+00:00",
                "ended_at": "2026-01-01T00:00:01+00:00",
                "duration_seconds": 1.0,
                "stages": {"validation": 0.1, "prompt_building": 0.2},
                "dry_run": False,
                "success": True,
            },
        },
        "warnings": [],
        "errors": [],
        "governance_result": sample_governance_payload,
        "token_usage": {
            "success": True,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "input_tokens": 120,
            "output_tokens": 80,
            "total_tokens": 200,
            "estimated": False,
            "source": "provider_usage",
            "execution_id": "exec-1",
            "module": "generation",
            "operation": "generation",
            "campaign_id": "campaign-1",
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
            "input_tokens": 120,
            "output_tokens": 80,
            "cached_input_tokens": 0,
            "total_tokens": 200,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "cached_input_cost": 0.0,
            "total_cost": 0.0,
            "estimated_tokens": False,
            "estimated_cost": True,
            "pricing_found": False,
            "pricing_version": "unknown",
            "pricing_source": "unknown",
            "execution_id": "exec-1",
            "module": "generation",
            "operation": "generation",
            "campaign_id": "campaign-1",
            "asset_type": "instagram_post",
            "metadata": {},
            "warnings": ["Pricing not found for provider/model."],
            "errors": [],
        },
        "execution_cost_summary": {"summary": {"total_cost": 0.0}},
        "module_cost_summary": {"summary": {"generation": {"total_cost": 0.0}}},
        "provider_cost_summary": {"summary": {"openai": {"total_cost": 0.0}}},
        "model_cost_summary": {"summary": {"gpt-4o-mini": {"total_cost": 0.0}}},
        "campaign_result": {
            "campaign_name": "sample_campaign",
            "campaign_type": "property_launch",
            "objective": "generate_leads",
            "brand": sample_generation_request["brand"],
            "audience": sample_generation_request["audience"],
            "location": sample_generation_request["location"],
            "strategy": {"cta_strategy": "trust-first"},
            "asset_plan": {"required_assets": ["instagram_post"]},
            "assets": {"instagram_post": {"status": "approved"}},
            "platform_plan": {"instagram": ["instagram_post"]},
            "content_sequence": [{"step": "awareness", "asset_type": "instagram_post"}],
            "governance_summary": {"status": "approved"},
        },
        "asset_coordination_result": {
            "brand": sample_generation_request["brand"],
            "campaign_type": "property_launch",
            "objective": "generate_leads",
            "asset_plan": {"required_assets": ["image_prompt"]},
            "asset_requirements": {"platform_requirements": {}},
            "assets": {"image_prompt": {"status": "approved"}},
            "missing_assets": [],
            "validation_result": {"valid": True, "warnings": [], "errors": []},
            "success": True,
            "warnings": [],
            "errors": [],
        },
        "exported_files": {"markdown": "/tmp/report.md"},
        "output_metadata": {"validation_status": "passed"},
    }
    bundle = engine.generate(payload, export=False)
    assert bundle["success"] is True
    assert bundle["consolidated_report"]["report_type"] == "consolidated"
    assert bundle["execution_report"]["metrics"]["execution_time_seconds"] == 1.0
    assert bundle["execution_report"]["metrics"]["total_cost"] == 0.0
    assert bundle["consolidated_report"]["metrics"]["total_cost"] == 0.0
    assert bundle["governance_report"]["metrics"]["status"] == "unknown"


def test_report_exporter_writes_safe_files(tmp_path: Path) -> None:
    exporter = ReportExporter(output_root=str(tmp_path))
    report = {
        "report_type": "consolidated",
        "title": "Consolidated Report",
        "summary": {"status": "success"},
        "metrics": {"execution_time_seconds": 1.23},
        "warnings": [],
        "errors": [],
        "metadata": {"brand": "sample_brand"},
        "sections": {},
        "generated_at": "2026-01-01T00:00:00+00:00",
    }
    exported = exporter.export(report, brand="sample_brand", report_name="demo_report", formats=["markdown", "json"])
    assert set(exported.keys()) == {"markdown", "json"}
    assert all(Path(path).exists() for path in exported.values())


def test_pipeline_attaches_reporting_when_enabled() -> None:
    config = PipelineConfig(enable_live_generation=False, enable_reporting=True)
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
            "extra_notes": "Test reporting path.",
        }
    )
    assert result["success"] is False
    assert "execution_report" in result
    assert "consolidated_report" in result
    assert result["metadata"].get("reporting", {}).get("report_types")
