"""Tests for workflow template definitions."""

from __future__ import annotations

from src.workflows.workflow_templates import build_workflow_templates, get_workflow_template_definition


def test_workflow_templates_include_expected_packages():
    templates = build_workflow_templates()

    assert "single_content_generation" in templates
    assert "image_prompt_workflow" in templates
    assert "video_script_workflow" in templates
    assert "creative_direction_workflow" in templates


def test_workflow_template_definition_has_steps():
    template = get_workflow_template_definition("full_campaign_package")

    assert template["steps"][0] == "load_context"
    assert "persist_results" in template["steps"]
