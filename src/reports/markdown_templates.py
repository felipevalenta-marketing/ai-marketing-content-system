"""Markdown report templates and section ordering."""

from __future__ import annotations

from typing import Any


def build_markdown_templates() -> dict[str, dict[str, Any]]:
    return {
        "workflow_report": {
            "name": "Workflow Report",
            "description": "Human-readable workflow execution summary.",
            "sections": [
                "title",
                "executive_summary",
                "workflow_summary",
                "workflow_snapshot",
                "generation_output",
                "campaign",
                "assets",
                "governance",
                "token_usage",
                "cost_usage",
                "storage",
                "warnings",
                "errors",
                "metadata",
            ],
        },
        "campaign_report": {
            "name": "Campaign Report",
            "description": "Human-readable campaign summary.",
            "sections": [
                "title",
                "executive_summary",
                "context",
                "campaign",
                "assets",
                "governance",
                "token_usage",
                "cost_usage",
                "metadata",
                "warnings",
                "errors",
            ],
        },
        "generation_report": {
            "name": "Generation Report",
            "description": "Human-readable generation summary.",
            "sections": [
                "title",
                "executive_summary",
                "context",
                "generation_output",
                "governance",
                "token_usage",
                "cost_usage",
                "warnings",
                "errors",
                "metadata",
            ],
        },
        "asset_report": {
            "name": "Asset Report",
            "description": "Human-readable asset coordination summary.",
            "sections": [
                "title",
                "executive_summary",
                "assets",
                "media",
                "workflow_snapshot",
                "campaign",
                "governance",
                "storage",
                "warnings",
                "errors",
                "metadata",
            ],
        },
        "governance_report": {
            "name": "Governance Report",
            "description": "Human-readable governance validation summary.",
            "sections": [
                "title",
                "executive_summary",
                "governance",
                "warnings",
                "errors",
                "metadata",
            ],
        },
        "tracking_report": {
            "name": "Tracking Report",
            "description": "Human-readable token tracking summary.",
            "sections": [
                "title",
                "executive_summary",
                "token_usage",
                "cost_usage",
                "metadata",
            ],
        },
        "cost_report": {
            "name": "Cost Report",
            "description": "Human-readable cost summary.",
            "sections": [
                "title",
                "executive_summary",
                "cost_usage",
                "token_usage",
                "metadata",
            ],
        },
        "storage_report": {
            "name": "Storage Report",
            "description": "Human-readable persistence summary.",
            "sections": [
                "title",
                "executive_summary",
                "storage",
                "metadata",
                "warnings",
                "errors",
            ],
        },
        "creative_direction_report": {
            "name": "Creative Direction Report",
            "description": "Human-readable creative direction summary.",
            "sections": [
                "title",
                "executive_summary",
                "creative_direction",
                "media",
                "governance",
                "metadata",
            ],
        },
        "media_report": {
            "name": "Media Report",
            "description": "Human-readable image and video media summary.",
            "sections": [
                "title",
                "executive_summary",
                "media",
                "creative_direction",
                "workflow_snapshot",
                "governance",
                "metadata",
            ],
        },
        "image_prompt_report": {
            "name": "Image Prompt Report",
            "description": "Human-readable image prompt summary.",
            "sections": [
                "title",
                "executive_summary",
                "media",
                "creative_direction",
                "governance",
                "metadata",
            ],
        },
        "image_prompt_validation_report": {
            "name": "Image Prompt Validation Report",
            "description": "Human-readable image prompt validation summary.",
            "sections": [
                "title",
                "executive_summary",
                "media",
                "creative_direction",
                "governance",
                "warnings",
                "errors",
                "metadata",
            ],
        },
        "visual_style_report": {
            "name": "Visual Style Report",
            "description": "Human-readable visual identity summary.",
            "sections": [
                "title",
                "executive_summary",
                "creative_direction",
                "media",
                "workflow_snapshot",
                "metadata",
            ],
        },
        "storyboard_report": {
            "name": "Storyboard Report",
            "description": "Human-readable storyboard summary.",
            "sections": [
                "title",
                "executive_summary",
                "media",
                "workflow_snapshot",
                "governance",
                "metadata",
            ],
        },
        "video_script_report": {
            "name": "Video Script Report",
            "description": "Human-readable video script summary.",
            "sections": [
                "title",
                "executive_summary",
                "media",
                "workflow_snapshot",
                "governance",
                "metadata",
            ],
        },
        "video_prompt_report": {
            "name": "Video Prompt Report",
            "description": "Human-readable video prompt summary.",
            "sections": [
                "title",
                "executive_summary",
                "media",
                "creative_direction",
                "workflow_snapshot",
                "governance",
                "metadata",
            ],
        },
        "execution_report": {
            "name": "Execution Report",
            "description": "Human-readable execution summary.",
            "sections": [
                "title",
                "executive_summary",
                "context",
                "workflow_summary",
                "workflow_snapshot",
                "generation_output",
                "governance",
                "token_usage",
                "cost_usage",
                "storage",
                "warnings",
                "errors",
                "metadata",
            ],
        },
        "executive_summary": {
            "name": "Executive Summary",
            "description": "Short client-friendly summary.",
            "sections": [
                "title",
                "executive_summary",
                "campaign",
                "assets",
                "workflow_snapshot",
                "governance",
                "token_usage",
                "cost_usage",
                "storage",
                "metadata",
            ],
        },
        "client_presentation_report": {
            "name": "Client Presentation Report",
            "description": "Client-ready presentation summary.",
            "sections": ["title", "executive_summary", "campaign", "assets", "media", "governance", "metadata"],
        },
        "pdf_export_report": {
            "name": "PDF Export Report",
            "description": "Future-ready PDF export summary.",
            "sections": ["title", "executive_summary", "campaign", "assets", "media", "governance", "metadata"],
        },
        "dashboard_report": {
            "name": "Dashboard Report",
            "description": "Dashboard-friendly report summary.",
            "sections": ["title", "executive_summary", "workflow_summary", "workflow_snapshot", "tracking", "cost_usage", "storage", "metadata"],
        },
        "audit_report": {
            "name": "Audit Report",
            "description": "Audit-oriented report summary.",
            "sections": ["title", "executive_summary", "governance", "workflow_snapshot", "tracking", "cost_usage", "storage", "warnings", "errors", "metadata"],
        },
        "performance_report": {
            "name": "Performance Report",
            "description": "Performance summary for operations.",
            "sections": ["title", "executive_summary", "workflow_summary", "workflow_snapshot", "tracking", "cost_usage", "storage", "metadata"],
        },
        "monthly_usage_report": {
            "name": "Monthly Usage Report",
            "description": "Monthly usage summary.",
            "sections": ["title", "executive_summary", "tracking", "cost_usage", "storage", "metadata"],
        },
    }


def get_markdown_template(report_type: str) -> dict[str, Any]:
    templates = build_markdown_templates()
    return templates.get(str(report_type).strip().lower(), templates["executive_summary"])


def list_supported_markdown_report_types() -> list[str]:
    return sorted(build_markdown_templates().keys())
