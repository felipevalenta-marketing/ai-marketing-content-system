"""Workflow templates and step ordering."""

from __future__ import annotations

from typing import Any


def build_workflow_templates() -> dict[str, dict[str, Any]]:
    return {
        "single_content_generation": {
            "name": "Single Content Generation",
            "description": "Generate and govern a single content item.",
            "required_inputs": ["brand", "platform", "content_type", "objective", "audience"],
            "optional_inputs": ["location", "property_type", "visual_style", "creative_direction", "extra_notes"],
            "approval_gates": [],
            "steps": [
                "load_context",
                "build_prompt",
                "generate_content",
                "parse_response",
                "format_output",
                "adapt_platform",
                "run_governance",
                "track_tokens",
                "track_costs",
                "build_report",
                "persist_results",
            ],
        },
        "campaign_generation": {
            "name": "Campaign Generation",
            "description": "Compose a campaign without media generation.",
            "required_inputs": ["brand", "campaign_type", "objective", "audience"],
            "optional_inputs": ["platforms", "assets", "location", "property_type", "extra_notes"],
            "approval_gates": ["governance_before_persistence"],
            "steps": [
                "load_context",
                "compose_campaign",
                "coordinate_assets",
                "run_governance",
                "track_tokens",
                "track_costs",
                "build_report",
                "persist_results",
            ],
        },
        "campaign_with_assets": {
            "name": "Campaign With Assets",
            "description": "Compose a campaign and coordinate assets.",
            "required_inputs": ["brand", "campaign_type", "objective", "audience"],
            "optional_inputs": ["platforms", "assets", "location", "property_type", "extra_notes"],
            "approval_gates": ["governance_before_persistence"],
            "steps": [
                "load_context",
                "compose_campaign",
                "coordinate_assets",
                "run_governance",
                "track_tokens",
                "track_costs",
                "build_report",
                "persist_results",
            ],
        },
        "image_prompt_workflow": {
            "name": "Image Prompt Workflow",
            "description": "Build an image prompt and relevant governance/reporting.",
            "required_inputs": ["brand", "platform", "content_type", "objective", "audience"],
            "optional_inputs": ["location", "property_type", "visual_style", "creative_direction", "aspect_ratio"],
            "approval_gates": [],
            "steps": [
                "load_context",
                "generate_image_prompt",
                "run_governance",
                "coordinate_assets",
                "build_report",
                "persist_results",
            ],
        },
        "video_script_workflow": {
            "name": "Video Script Workflow",
            "description": "Build a structured video script and storyboard.",
            "required_inputs": ["brand", "platform", "content_type", "objective", "audience"],
            "optional_inputs": ["location", "property_type", "visual_style", "creative_direction", "duration", "video_type"],
            "approval_gates": [],
            "steps": [
                "load_context",
                "generate_video_script",
                "run_governance",
                "coordinate_assets",
                "build_report",
                "persist_results",
            ],
        },
        "creative_direction_workflow": {
            "name": "Creative Direction Workflow",
            "description": "Build a creative direction package for downstream media.",
            "required_inputs": ["brand", "campaign_type", "objective", "audience"],
            "optional_inputs": ["platforms", "visual_style", "creative_direction"],
            "approval_gates": [],
            "steps": [
                "load_context",
                "generate_creative_direction",
                "run_governance",
                "build_report",
                "persist_results",
            ],
        },
        "full_campaign_package": {
            "name": "Full Campaign Package",
            "description": "Build a full campaign pack across content, media, and coordination.",
            "required_inputs": ["brand", "campaign_type", "objective", "audience"],
            "optional_inputs": ["platform", "platforms", "location", "property_type", "visual_style", "creative_direction", "assets"],
            "approval_gates": ["governance_before_persistence"],
            "steps": [
                "load_context",
                "generate_creative_direction",
                "compose_campaign",
                "generate_content",
                "generate_image_prompt",
                "generate_video_script",
                "coordinate_assets",
                "run_governance",
                "track_tokens",
                "track_costs",
                "build_report",
                "persist_results",
            ],
        },
        "validation_only_workflow": {
            "name": "Validation Only Workflow",
            "description": "Run validation and reporting without generation.",
            "required_inputs": ["brand", "platform", "content_type", "objective", "audience"],
            "optional_inputs": [],
            "approval_gates": [],
            "steps": ["load_context", "run_governance", "build_report"],
        },
        "reporting_only_workflow": {
            "name": "Reporting Only Workflow",
            "description": "Build a report from existing state or payloads.",
            "required_inputs": ["brand"],
            "optional_inputs": [],
            "approval_gates": [],
            "steps": ["build_report"],
        },
    }


def get_workflow_template_definition(workflow_type: str) -> dict[str, Any]:
    return build_workflow_templates().get(workflow_type, {})

