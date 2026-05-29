"""Render markdown reports safely and deterministically."""

from __future__ import annotations

from typing import Any
import re


def render_heading(text: str, level: int = 2) -> str:
    """Render a markdown heading."""

    safe_level = max(1, min(int(level or 2), 6))
    return f"{'#' * safe_level} {str(text).strip()}"


def render_bullets(items: list[Any]) -> str:
    """Render a bullet list from simple values or mappings."""

    if not items:
        return ""
    lines: list[str] = []
    for item in items:
        if isinstance(item, dict):
            for key, value in item.items():
                lines.append(f"- **{_format_label(key)}**: {_format_value(value)}")
        else:
            text = _format_value(item)
            if text:
                lines.append(f"- {text}")
    return "\n".join(lines).strip()


def render_table(rows: list[dict[str, Any]]) -> str:
    """Render a simple markdown table."""

    if not rows:
        return ""
    headers: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in row.keys():
            label = _format_label(key)
            if label not in headers:
                headers.append(label)
    if not headers:
        return ""
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        values = [_escape_table_cell(_format_value(row.get(_normalize_label(label), row.get(label, "")))) for label in headers]
        body_lines.append("| " + " | ".join(values) + " |")
    return "\n".join([header_line, separator_line, *body_lines]).strip()


def render_code_block(content: str, language: str = "") -> str:
    """Render a fenced code block."""

    fence_language = str(language or "").strip()
    safe_content = str(content or "").rstrip()
    if fence_language:
        return f"```{fence_language}\n{safe_content}\n```"
    return f"```\n{safe_content}\n```"


def render_report(title: str, sections: list[str]) -> str:
    """Render a complete markdown report."""

    lines = [render_heading(title, level=1), ""]
    cleaned_sections = [clean_markdown(section) for section in sections if str(section or "").strip()]
    for index, section in enumerate(cleaned_sections):
        lines.append(section)
        if index < len(cleaned_sections) - 1:
            lines.append("")
    return clean_markdown("\n".join(lines))


def clean_markdown(markdown: str) -> str:
    """Normalize whitespace and blank lines in markdown output."""

    text = str(markdown or "")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _format_label(value: Any) -> str:
    text = str(value or "").replace("_", " ").strip()
    return text.title() if text else "Value"


def _normalize_label(label: str) -> str:
    return str(label or "").strip().lower().replace(" ", "_")


def _format_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(_format_value(item) for item in value if _format_value(item))
    if isinstance(value, dict):
        parts = [f"{_format_label(key)}: {_format_value(item)}" for key, item in value.items() if _format_value(item)]
        return "; ".join(parts)
    return str(value).strip()


def _escape_table_cell(value: str) -> str:
    text = str(value or "")
    return text.replace("|", "\\|").replace("\n", " ")

