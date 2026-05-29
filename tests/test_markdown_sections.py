from __future__ import annotations

from src.reports.markdown_sections import (
    build_asset_section,
    build_campaign_section,
    build_context_section,
    build_cost_usage_section,
    build_executive_summary_section,
    build_generation_output_section,
    build_governance_section,
    build_metadata_section,
    build_storage_section,
    build_title_section,
    build_token_usage_section,
    build_tracking_section,
    build_warnings_section,
    build_workflow_summary_section,
)


def test_markdown_sections_handle_missing_data() -> None:
    assert build_asset_section({}) == ""
    assert build_campaign_section({}) == ""
    assert build_context_section({}) == ""
    assert build_generation_output_section({}) == ""
    assert build_metadata_section({}) == ""
    assert build_storage_section({}) == ""
    assert build_warnings_section({}) == ""


def test_markdown_sections_render_expected_content(sample_workflow_request: dict, sample_token_usage: dict, sample_cost_usage: dict) -> None:
    payload = {
        "title": "Campaign Workflow Report",
        "brand": sample_workflow_request["brand"],
        "platform": sample_workflow_request["platform"],
        "campaign_type": sample_workflow_request["campaign_type"],
        "content_type": sample_workflow_request["content_type"],
        "objective": sample_workflow_request["objective"],
        "audience": sample_workflow_request["audience"],
        "location": sample_workflow_request["location"],
        "property_type": sample_workflow_request["property_type"],
        "visual_style": sample_workflow_request["visual_style"],
        "creative_direction": sample_workflow_request["creative_direction"],
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
        "token_summary": sample_token_usage,
        "cost_summary": sample_cost_usage,
        "storage_summary": {"storage_root": "data", "records_saved": 3, "markdown_saved": True, "stored_record_ids": ["a", "b", "c"]},
        "warnings": ["Sample warning"],
        "metadata": {"brand": sample_workflow_request["brand"], "platform": sample_workflow_request["platform"]},
    }

    assert "Overview" in build_title_section(payload)
    assert "Workflow Overview" in build_workflow_summary_section(payload)
    assert "Token Usage" in build_token_usage_section(payload)
    assert "Cost Usage" in build_cost_usage_section(payload)
    assert "Tracking" in build_tracking_section(payload)
    assert "Executive Summary" in build_executive_summary_section(payload)
    assert "Governance" in build_governance_section({"governance_result": {"status": "approved", "overall_score": 90}})

