from __future__ import annotations

from src.reports.markdown_templates import build_markdown_templates, get_markdown_template, list_supported_markdown_report_types


def test_markdown_templates_include_core_report_types() -> None:
    supported = list_supported_markdown_report_types()

    assert "workflow_report" in supported
    assert "campaign_report" in supported
    assert "generation_report" in supported
    assert "executive_summary" in supported
    assert "image_prompt_report" in supported
    assert "image_prompt_validation_report" in supported
    assert "visual_style_report" in supported
    assert "storyboard_report" in supported
    assert "video_script_report" in supported
    assert "video_prompt_report" in supported


def test_markdown_templates_return_section_order() -> None:
    template = get_markdown_template("workflow_report")

    assert template["name"] == "Workflow Report"
    assert "title" in template["sections"]
    assert "workflow_summary" in template["sections"]


def test_markdown_templates_are_dict_based() -> None:
    templates = build_markdown_templates()

    assert isinstance(templates, dict)
    assert all(isinstance(value, dict) for value in templates.values())
