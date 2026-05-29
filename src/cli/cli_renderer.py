"""Render CLI command results in terminal, markdown, or JSON formats."""

from __future__ import annotations

from typing import Any
import json


SENSITIVE_KEYS = {
    "api_key",
    "openai_api_key",
    "raw_response",
    "secret",
}


def render_cli_result(result: dict[str, Any], output_format: str = "terminal") -> str:
    """Render a command result to the requested output format."""

    format_key = (output_format or "terminal").strip().lower()
    if format_key == "json":
        return render_json(result)
    if format_key == "markdown":
        return render_markdown(result)
    return render_terminal(result)


def render_json(result: dict[str, Any]) -> str:
    """Return a JSON-safe representation suitable for copy/paste."""

    return json.dumps(_sanitize(result), indent=2, ensure_ascii=False, default=str)


def render_markdown(result: dict[str, Any]) -> str:
    """Return a markdown-formatted CLI summary."""

    clean = _sanitize(result)
    lines = [
        f"# {str(clean.get('command', 'command')).replace('_', ' ').title()}",
        "",
        f"- **Status**: {_status_label(clean)}",
        f"- **Mode**: {str(clean.get('mode', 'live')).replace('_', ' ')}",
    ]
    for key in ("brand", "platform", "content_type", "campaign_type", "objective", "audience", "location"):
        value = clean.get(key)
        if value:
            lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")

    lines.extend(_render_summary_markdown(clean))
    lines.extend(_render_report_markdown(clean.get("payload")))
    lines.extend(_render_kv_markdown("Warnings", clean.get("warnings", [])))
    lines.extend(_render_kv_markdown("Errors", clean.get("errors", [])))
    return "\n".join(lines).strip()


def render_terminal(result: dict[str, Any]) -> str:
    """Return a readable terminal summary."""

    clean = _sanitize(result)
    lines = [
        f"{str(clean.get('command', 'command')).replace('_', ' ').title()}",
        f"Status: {_status_label(clean)}",
        f"Mode: {str(clean.get('mode', 'live')).replace('_', ' ')}",
    ]
    for key in ("brand", "platform", "content_type", "campaign_type", "objective", "audience", "location"):
        value = clean.get(key)
        if value:
            lines.append(f"{key.replace('_', ' ').title()}: {value}")

    summary = clean.get("summary")
    if isinstance(summary, dict) and summary:
        lines.append("")
        lines.append("Summary:")
        for key, value in summary.items():
            lines.append(f"  - {key.replace('_', ' ').title()}: {_format_value(value)}")

    payload = clean.get("payload")
    payload_lines = _render_payload_lines(payload, terminal=True)
    if payload_lines:
        lines.extend(payload_lines)
    report_lines = _render_report_terminal(payload)
    if report_lines:
        lines.extend(report_lines)

    lines.extend(_render_kv_terminal("Warnings", clean.get("warnings", [])))
    lines.extend(_render_kv_terminal("Errors", clean.get("errors", [])))
    return "\n".join(lines).strip()


def _render_summary_markdown(result: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    summary = result.get("summary")
    if isinstance(summary, dict) and summary:
        lines.extend(["", "## Summary"])
        for key, value in summary.items():
            lines.append(f"- **{key.replace('_', ' ').title()}**: {_format_value(value)}")

    payload_lines = _render_payload_lines(result.get("payload"), terminal=False)
    if payload_lines:
        lines.extend(["", "## Payload Preview"])
        lines.extend(payload_lines)
    return lines


def _render_kv_markdown(title: str, values: Any) -> list[str]:
    items = _normalize_list(values)
    if not items:
        return []
    lines = ["", f"## {title}"]
    lines.extend(f"- {item}" for item in items)
    return lines


def _render_kv_terminal(title: str, values: Any) -> list[str]:
    items = _normalize_list(values)
    if not items:
        return []
    lines = [""]
    lines.append(f"{title}:")
    lines.extend(f"  - {item}" for item in items)
    return lines


def _normalize_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if values in (None, "", {}, []):
        return []
    return [str(values).strip()]


def _status_label(result: dict[str, Any]) -> str:
    if result.get("success") is True:
        return "success"
    if result.get("success") is False:
        return "failed"
    return "unknown"


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                continue
            sanitized[key] = _sanitize(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value


def _format_value(value: Any) -> str:
    """Format nested values for human-readable output."""

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _render_payload_lines(payload: Any, terminal: bool) -> list[str]:
    """Render payload lines only when there is meaningful content."""

    if not isinstance(payload, dict) or not payload:
        return []

    keys = (
        "prompt_summary",
        "planned_execution",
        "planned_route",
        "checks",
        "validation_result",
        "governance_result",
        "context_summary",
        "asset_plan",
        "asset_requirements",
        "strategy",
        "platform_plan",
        "content_sequence",
        "missing_assets",
        "export_paths",
        "report_export_paths",
        "execution_report",
        "governance_report",
        "campaign_report",
        "asset_report",
        "export_report",
        "consolidated_report",
        "reporting",
        "workflow_result",
        "workflow_id",
        "workflow_type",
        "workflow_status",
        "workflow_step_summary",
        "workflow_storage_summary",
        "markdown_report_path",
        "markdown_report",
        "markdown_sections",
        "markdown_validation",
        "campaign_name",
        "campaign_type",
        "status",
        "overall_score",
        "approval_status",
    )
    lines: list[str] = []
    for key in keys:
        value = payload.get(key)
        if value in (None, "", [], {}):
            continue
        label = key.replace("_", " ").title()
        prefix = "  - " if terminal else "- **"
        suffix = "" if terminal else "**"
        if terminal:
            lines.append(f"{prefix}{label}: {_format_value(value)}")
        else:
            lines.append(f"{prefix}{label}{suffix}: {_format_value(value)}")
    if terminal and lines:
        lines.insert(0, "")
        lines.insert(1, "Payload:")
    return lines


def _render_report_markdown(payload: Any) -> list[str]:
    """Render an attached report bundle as markdown when available."""

    if not isinstance(payload, dict):
        return []
    markdown_report = payload.get("markdown_report") if isinstance(payload.get("markdown_report"), dict) else {}
    reporting = payload.get("reporting")
    if not isinstance(markdown_report, dict) and isinstance(reporting, dict):
        markdown_report = reporting.get("markdown_report") if isinstance(reporting.get("markdown_report"), dict) else {}
    if not isinstance(markdown_report, dict) and isinstance(reporting, dict):
        markdown_report = {}
    report_markdown = markdown_report.get("markdown") if isinstance(markdown_report, dict) else None
    if (not isinstance(report_markdown, str) or not report_markdown.strip()) and isinstance(reporting, dict):
        report_markdown = reporting.get("rendered_markdown")
    if not isinstance(report_markdown, str) or not report_markdown.strip():
        return []
    return ["", "## Report", "", report_markdown.strip()]


def _render_report_terminal(payload: Any) -> list[str]:
    """Render an attached report bundle as a terminal preview when available."""

    if not isinstance(payload, dict):
        return []
    reporting = payload.get("reporting")
    if not isinstance(reporting, dict):
        return []
    report_text = reporting.get("rendered_text")
    if not isinstance(report_text, str) or not report_text.strip():
        return []
    lines = ["", "Report Preview:"]
    lines.extend(f"  {line}" for line in report_text.strip().splitlines()[:20])
    return lines
