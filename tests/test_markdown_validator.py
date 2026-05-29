from __future__ import annotations

from src.reports.markdown_validator import MarkdownValidator


def test_markdown_validator_accepts_safe_report() -> None:
    validator = MarkdownValidator()
    result = validator.validate(
        {
            "report_type": "workflow_report",
            "title": "Workflow Report",
            "markdown": "# Workflow Report\n\n## Executive Summary\nSafe content.",
            "metadata": {"brand": "wenzel_partner"},
            "export_path": "outputs/reports/markdown/wenzel_partner/workflow_report/demo.md",
        }
    )

    assert result["valid"] is True


def test_markdown_validator_allows_token_and_cost_metrics() -> None:
    validator = MarkdownValidator()
    result = validator.validate(
        {
            "report_type": "tracking_report",
            "title": "Tracking Report",
            "markdown": "# Tracking Report\n\n## Token Usage\n| Metric | Value |\n| --- | --- |\n| Input Tokens | 120 |\n\n## Cost Usage\n| Metric | Value |\n| --- | --- |\n| Total Cost | 0.030000 |",
            "metadata": {
                "brand": "wenzel_partner",
                "token_summary": {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 120, "output_tokens": 30, "total_tokens": 150},
                "cost_summary": {"provider": "openai", "model": "gpt-4o-mini", "currency": "USD", "total_cost": 0.03},
            },
            "export_path": "outputs/reports/markdown/wenzel_partner/tracking_report/demo.md",
        }
    )

    assert result["valid"] is True


def test_markdown_validator_rejects_secrets() -> None:
    validator = MarkdownValidator()
    result = validator.validate(
        {
            "report_type": "workflow_report",
            "title": "Workflow Report",
            "markdown": "OPENAI_API_KEY=sk-test-secret",
            "metadata": {"brand": "wenzel_partner"},
            "export_path": "outputs/reports/markdown/wenzel_partner/workflow_report/demo.md",
        }
    )

    assert result["valid"] is False
    assert any("sensitive" in error.lower() for error in result["errors"])


def test_markdown_validator_rejects_unsafe_path() -> None:
    validator = MarkdownValidator()
    result = validator.validate(
        {
            "report_type": "workflow_report",
            "title": "Workflow Report",
            "markdown": "# Workflow Report",
            "metadata": {"brand": "wenzel_partner"},
            "export_path": "../outside.md",
        }
    )

    assert result["valid"] is False
    assert any("unsafe" in error.lower() for error in result["errors"])
