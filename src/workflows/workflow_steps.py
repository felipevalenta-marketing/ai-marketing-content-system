"""Workflow step definitions."""

from __future__ import annotations

from typing import Any


def build_workflow_step_definitions() -> dict[str, dict[str, Any]]:
    """Return reusable workflow step definitions."""

    return {
        "load_context": {
            "name": "Load Context",
            "description": "Load brand context and summarize knowledge for the workflow.",
            "required_inputs": ["brand"],
            "expected_outputs": ["context"],
            "dependency_rules": [],
            "default_enabled": True,
        },
        "build_prompt": {
            "name": "Build Prompt",
            "description": "Build a prompt payload for the main content path.",
            "required_inputs": ["brand", "platform", "content_type"],
            "expected_outputs": ["prompt_payload"],
            "dependency_rules": ["load_context"],
            "default_enabled": True,
        },
        "generate_content": {
            "name": "Generate Content",
            "description": "Call the OpenAI generation layer through the existing pipeline.",
            "required_inputs": ["prompt_payload"],
            "expected_outputs": ["ai_response"],
            "dependency_rules": ["build_prompt"],
            "default_enabled": True,
        },
        "parse_response": {
            "name": "Parse Response",
            "description": "Parse the generated response using the existing response parser.",
            "required_inputs": ["ai_response"],
            "expected_outputs": ["parsed_output"],
            "dependency_rules": ["generate_content"],
            "default_enabled": True,
        },
        "format_output": {
            "name": "Format Output",
            "description": "Format the parsed output using the existing output formatter.",
            "required_inputs": ["parsed_output", "content_type"],
            "expected_outputs": ["formatted_output"],
            "dependency_rules": ["parse_response"],
            "default_enabled": True,
        },
        "adapt_platform": {
            "name": "Adapt Platform",
            "description": "Adapt formatted output to target platforms.",
            "required_inputs": ["formatted_output", "platforms"],
            "expected_outputs": ["adaptation_result"],
            "dependency_rules": ["format_output"],
            "default_enabled": True,
        },
        "run_governance": {
            "name": "Run Governance",
            "description": "Evaluate brand, platform, and factual safety using the governance engine.",
            "required_inputs": ["formatted_output"],
            "expected_outputs": ["governance_result"],
            "dependency_rules": ["format_output"],
            "default_enabled": True,
        },
        "compose_campaign": {
            "name": "Compose Campaign",
            "description": "Compose campaign packs using the campaign composer.",
            "required_inputs": ["campaign_type", "brand"],
            "expected_outputs": ["campaign_result"],
            "dependency_rules": ["load_context"],
            "default_enabled": True,
        },
        "coordinate_assets": {
            "name": "Coordinate Assets",
            "description": "Coordinate asset plans and missing assets.",
            "required_inputs": ["campaign_type", "brand"],
            "expected_outputs": ["asset_coordination_result"],
            "dependency_rules": ["compose_campaign"],
            "default_enabled": True,
        },
        "generate_image_prompt": {
            "name": "Generate Image Prompt",
            "description": "Generate structured image prompt guidance.",
            "required_inputs": ["brand", "platform"],
            "expected_outputs": ["image_prompt_result"],
            "dependency_rules": ["load_context"],
            "default_enabled": True,
        },
        "generate_video_script": {
            "name": "Generate Video Script",
            "description": "Generate a short-form video script and storyboard.",
            "required_inputs": ["brand", "platform"],
            "expected_outputs": ["video_script_result"],
            "dependency_rules": ["load_context"],
            "default_enabled": True,
        },
        "generate_creative_direction": {
            "name": "Generate Creative Direction",
            "description": "Generate a visual identity and creative direction package.",
            "required_inputs": ["brand", "campaign_type"],
            "expected_outputs": ["creative_direction_result"],
            "dependency_rules": ["load_context"],
            "default_enabled": True,
        },
        "track_tokens": {
            "name": "Track Tokens",
            "description": "Normalize and summarize token usage.",
            "required_inputs": [],
            "expected_outputs": ["token_usage", "execution_token_summary"],
            "dependency_rules": ["generate_content"],
            "default_enabled": True,
        },
        "track_costs": {
            "name": "Track Costs",
            "description": "Estimate and summarize AI usage cost from token usage.",
            "required_inputs": ["token_usage"],
            "expected_outputs": ["cost_usage", "execution_cost_summary"],
            "dependency_rules": ["track_tokens"],
            "default_enabled": True,
        },
        "build_report": {
            "name": "Build Report",
            "description": "Build analytics reports using the existing reporting engine.",
            "required_inputs": [],
            "expected_outputs": ["reporting"],
            "dependency_rules": [],
            "default_enabled": True,
        },
        "persist_results": {
            "name": "Persist Results",
            "description": "Persist safe workflow records through the storage manager.",
            "required_inputs": [],
            "expected_outputs": ["persistence_result", "storage_summary"],
            "dependency_rules": ["build_report"],
            "default_enabled": True,
        },
        "export_outputs": {
            "name": "Export Outputs",
            "description": "Export workflow outputs when explicitly enabled.",
            "required_inputs": [],
            "expected_outputs": ["export_summary"],
            "dependency_rules": ["build_report"],
            "default_enabled": False,
        },
        "approval_gate": {
            "name": "Approval Gate",
            "description": "Represent a human approval checkpoint.",
            "required_inputs": ["governance_result"],
            "expected_outputs": ["approval_status"],
            "dependency_rules": ["run_governance"],
            "default_enabled": True,
        },
    }


def get_step_definition(step_type: str) -> dict[str, Any]:
    return build_workflow_step_definitions().get(step_type, {})

