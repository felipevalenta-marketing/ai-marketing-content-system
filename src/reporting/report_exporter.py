"""Export analytics reports safely to disk."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime
import json

from src.reporting.report_renderer import ReportRenderer
from src.reporting.report_metrics import safe_filename, safe_text
from src.utils.logger import get_logger


class ReportExporter:
    """Write report payloads to markdown and JSON files."""

    def __init__(self, output_root: str = "outputs/reports", logger: Any | None = None) -> None:
        self.output_root = Path(output_root)
        self.logger = logger or get_logger(self.__class__.__name__)
        self.renderer = ReportRenderer()

    def export(
        self,
        report: dict[str, Any],
        brand: str,
        report_name: str | None = None,
        formats: list[str] | None = None,
    ) -> dict[str, str]:
        """Export a report in the requested formats."""

        formats = formats or ["markdown", "json"]
        report_type = safe_filename(str(report.get("report_type", "report")), fallback="report")
        brand_key = safe_filename(brand or "unknown_brand", fallback="unknown_brand")
        report_key = safe_filename(report_name or safe_text(report.get("title", "report"), limit=80), fallback=report_type)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        export_dir = self.output_root / brand_key / report_type
        export_dir.mkdir(parents=True, exist_ok=True)
        base_name = f"{timestamp}_{report_key}"
        exported: dict[str, str] = {}

        if "markdown" in formats:
            path = self._unique_path(export_dir / f"{base_name}.md")
            path.write_text(self.renderer.render_markdown(report), encoding="utf-8")
            exported["markdown"] = str(path)

        if "json" in formats:
            path = self._unique_path(export_dir / f"{base_name}.json")
            path.write_text(json.dumps(self.renderer.render_json(report), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            exported["json"] = str(path)

        return exported

    def _unique_path(self, path: Path) -> Path:
        """Ensure exports never overwrite existing files."""

        if not path.exists():
            return path
        index = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate
            index += 1
