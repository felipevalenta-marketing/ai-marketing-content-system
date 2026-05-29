"""Tests for workflow registry helpers."""

from __future__ import annotations

from src.workflows.workflow_registry import get_workflow_template, is_supported_workflow_type, list_workflow_templates


def test_workflow_registry_lists_supported_types():
    workflow_types = list_workflow_templates()

    assert "single_content_generation" in workflow_types
    assert "full_campaign_package" in workflow_types


def test_workflow_registry_returns_template():
    template = get_workflow_template("full_campaign_package")

    assert template["steps"]
    assert template["required_inputs"]
    assert template["name"]


def test_workflow_registry_reports_support():
    assert is_supported_workflow_type("campaign_generation") is True
    assert is_supported_workflow_type("unsupported_workflow") is False
