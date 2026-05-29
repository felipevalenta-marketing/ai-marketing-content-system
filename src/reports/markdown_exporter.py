"""Export markdown reports to disk safely."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from src.reports.markdown_contracts import utc_now_iso
from src.reports.markdown_utils import safe_filename, safe_text
from src.reports.markdown_validator import MarkdownValidator
from src.storage.json_store import read_json, write_json
from src.utils.logger import get_logger, log_warning


class MarkdownExporter:
    """Write markdown reports to a safe local folder."""

    def __init__(self, output_root: str | Path = "outputs/reports/markdown", logger: Any | None = None) -> None:
        self.output_root = Path(output_root)
        self.logger = logger or get_logger(self.__class__.__name__)
        self.validator = MarkdownValidator()

    def export_markdown(self, markdown: str, metadata: dict[str, Any], overwrite: bool = False) -> dict[str, Any]:
        """Export a markdown report to a file."""

        path = self.build_export_path(metadata)
        validation = self.validator.validate({"report_type": metadata.get("report_type", ""), "title": metadata.get("title", ""), "markdown": markdown, "export_path": str(path), "metadata": metadata})
        if not validation["valid"]:
            return {
                "success": False,
                "path": "",
                "markdown": markdown,
                "metadata": metadata,
                "warnings": validation.get("warnings", []),
                "errors": validation.get("errors", []),
            }
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and not overwrite:
                path = self._unique_path(path)
            path.write_text(str(markdown or ""), encoding="utf-8")
            index_result = self._update_index(metadata, str(path))
            warnings = list(validation.get("warnings", [])) + list(index_result.get("warnings", []))
            return {
                "success": True,
                "path": str(path),
                "markdown": markdown,
                "metadata": metadata,
                "warnings": warnings,
                "errors": [],
                "index_path": index_result.get("path", ""),
                "report_id": index_result.get("report_id", ""),
                "index_result": index_result,
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            log_warning(self.logger, f"Markdown export failed: {exc}")
            return {"success": False, "path": "", "markdown": markdown, "metadata": metadata, "warnings": list(validation.get("warnings", [])), "errors": [str(exc)]}

    def build_export_path(self, metadata: dict[str, Any]) -> Path:
        """Build a safe export path for a markdown report."""

        report_type = safe_filename(safe_text(metadata.get("report_type", "report"), limit=80), fallback="report")
        brand = safe_filename(safe_text(metadata.get("brand", "unknown_brand"), limit=80), fallback="unknown_brand")
        title = safe_filename(safe_text(metadata.get("title") or metadata.get("report_name") or report_type, limit=80), fallback=report_type)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return self.output_root / brand / report_type / f"{timestamp}_{title}.md"

    def _unique_path(self, path: Path) -> Path:
        if not path.exists():
            return path
        index = 1
        while True:
            candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    def _update_index(self, metadata: dict[str, Any], export_path: str) -> dict[str, Any]:
        """Update the markdown report index in a deterministic way."""

        try:
            index_path = self.output_root / "index.json"
            existing = read_json(index_path)
            records = []
            if existing.get("success") and isinstance(existing.get("record"), dict):
                records = list(existing["record"].get("records", []))
            report_id = safe_text(metadata.get("report_id") or self._build_report_id(metadata), limit=120)
            generated_at = safe_text(metadata.get("generated_at") or utc_now_iso(), limit=80)
            entry = {
                "report_id": report_id,
                "report_type": safe_text(metadata.get("report_type"), limit=80),
                "title": safe_text(metadata.get("title") or metadata.get("report_name") or metadata.get("report_type"), limit=160),
                "export_path": safe_text(export_path, limit=260),
                "generated_at": generated_at,
                "brand": safe_text(metadata.get("brand"), limit=80),
                "workflow_id": safe_text(metadata.get("workflow_id"), limit=120),
            }
            records = [item for item in records if not isinstance(item, dict) or item.get("report_id") != report_id]
            records.append(entry)
            records = sorted(
                [item for item in records if isinstance(item, dict)],
                key=lambda item: (safe_text(item.get("generated_at"), limit=80), safe_text(item.get("report_id"), limit=120)),
                reverse=True,
            )
            payload = {"updated_at": utc_now_iso(), "records": records[:1000]}
            write_result = write_json(index_path, payload, overwrite=True)
            return {
                "success": bool(write_result.get("success")),
                "path": str(index_path),
                "report_id": report_id,
                "warnings": list(existing.get("warnings", [])) if isinstance(existing, dict) else [],
                "errors": list(write_result.get("errors", [])),
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {"success": False, "path": "", "report_id": "", "warnings": [], "errors": [str(exc)]}

    def _build_report_id(self, metadata: dict[str, Any]) -> str:
        timestamp = safe_text(metadata.get("generated_at") or utc_now_iso(), limit=80).replace(":", "-")
        return safe_filename(
            f"{metadata.get('brand', 'unknown_brand')}_{metadata.get('report_type', 'report')}_{metadata.get('title', metadata.get('report_name', 'report'))}_{timestamp}",
            fallback="report",
        )
