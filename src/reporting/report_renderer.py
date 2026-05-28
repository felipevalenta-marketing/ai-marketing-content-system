"""Render analytics reports in terminal, markdown, and structured formats."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_list, safe_text


class ReportRenderer:
    """Render report payloads for humans and automation."""

    def render(self, report: dict[str, Any], output_format: str = "terminal") -> str | dict[str, Any]:
        """Render a report to the requested format."""

        format_key = safe_text(output_format, limit=40).lower()
        if format_key == "json":
            return self.render_json(report)
        if format_key == "markdown":
            return self.render_markdown(report)
        return self.render_terminal(report)

    def render_terminal(self, report: dict[str, Any]) -> str:
        """Render a report as a readable terminal summary."""

        clean = self.render_json(report)
        lines = [
            f"{safe_text(clean.get('title', 'Report'), limit=80)}",
            f"Type: {safe_text(clean.get('report_type', 'report'), limit=80)}",
        ]
        lines.extend(self._render_summary_lines(clean.get("summary"), bullet_prefix="  - "))
        lines.extend(self._render_metrics_lines(clean.get("metrics"), bullet_prefix="  - "))
        lines.extend(self._render_summary_lines(clean.get("metadata"), bullet_prefix="  - "))
        lines.extend(self._render_list_lines("Warnings", clean.get("warnings"), prefix="  - "))
        lines.extend(self._render_list_lines("Errors", clean.get("errors"), prefix="  - "))
        lines.extend(self._render_sections_lines(clean.get("sections"), terminal=True))
        return "\n".join(lines).strip()

    def render_markdown(self, report: dict[str, Any]) -> str:
        """Render a report as markdown."""

        clean = self.render_json(report)
        lines = [
            f"# {safe_text(clean.get('title', 'Report'), limit=120)}",
            "",
            f"- **Type**: {safe_text(clean.get('report_type', 'report'), limit=80)}",
            f"- **Generated At**: {safe_text(clean.get('generated_at', ''), limit=120)}",
        ]
        lines.extend(self._render_summary_lines(clean.get("summary"), bullet_prefix="- **", suffix="**"))
        lines.extend(self._render_metrics_lines(clean.get("metrics"), bullet_prefix="- **", suffix="**"))
        lines.extend(self._render_summary_lines(clean.get("metadata"), bullet_prefix="- **", suffix="**"))
        lines.extend(self._render_list_lines("Warnings", clean.get("warnings"), markdown=True))
        lines.extend(self._render_list_lines("Errors", clean.get("errors"), markdown=True))
        lines.extend(self._render_sections_lines(clean.get("sections"), terminal=False))
        return "\n".join(lines).strip()

    def render_json(self, report: dict[str, Any]) -> dict[str, Any]:
        """Return a JSON-safe structured report."""

        return self._sanitize(report)

    def _render_summary_lines(self, summary: Any, bullet_prefix: str, suffix: str = "") -> list[str]:
        if not isinstance(summary, dict) or not summary:
            return []
        lines: list[str] = [""]
        lines.append("Summary:")
        for key, value in summary.items():
            label = key.replace("_", " ").title()
            lines.append(f"{bullet_prefix}{label}{suffix}: {safe_text(value, limit=200)}")
        return lines

    def _render_metrics_lines(self, metrics: Any, bullet_prefix: str, suffix: str = "") -> list[str]:
        if not isinstance(metrics, dict) or not metrics:
            return []
        lines: list[str] = [""]
        lines.append("Metrics:")
        for key, value in metrics.items():
            label = key.replace("_", " ").title()
            lines.append(f"{bullet_prefix}{label}{suffix}: {safe_text(value, limit=200)}")
        return lines

    def _render_list_lines(self, title: str, values: Any, markdown: bool = False, prefix: str = "- ") -> list[str]:
        items = safe_list(values)
        items = [safe_text(item, limit=240) for item in items if safe_text(item, limit=240)]
        if not items:
            return []
        if markdown:
            lines = ["", f"## {title}"]
            lines.extend(f"- {item}" for item in items)
            return lines
        return ["", f"{title}:"] + [f"{prefix}{item}" for item in items]

    def _render_sections_lines(self, sections: Any, terminal: bool) -> list[str]:
        if not isinstance(sections, dict) or not sections:
            return []
        lines: list[str] = ["", "Sections:" if terminal else ""]
        for key, section in sections.items():
            label = key.replace("_", " ").title()
            if terminal:
                lines.append(f"  - {label}: {safe_text(section, limit=300)}")
            else:
                lines.append(f"## {label}")
                lines.append(f"{safe_text(section, limit=500)}")
                lines.append("")
        return [line for line in lines if line != "" or not terminal]

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {str(key): self._sanitize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return value
