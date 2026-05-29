"""Export formatted outputs to markdown and JSON files."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime
import json

from src.output.output_renderer import OutputRenderer
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_warning


class OutputExporter:
    """Write structured outputs to disk safely."""

    def __init__(self, output_root: str = "outputs", logger: Any | None = None) -> None:
        self.output_root = Path(output_root)
        self.logger = logger or get_logger(self.__class__.__name__)
        self.renderer = OutputRenderer(logger=self.logger)

    def export(
        self,
        brand: str,
        content_type: str,
        output: dict[str, Any],
        metadata: dict[str, Any],
        validation_result: dict[str, Any],
        formats: list[str] | None = None,
    ) -> dict[str, str]:
        """Export the output as markdown and/or JSON."""

        formats = formats or ["markdown", "json"]
        brand_key = normalize_key(brand or "unknown_brand")
        content_key = normalize_key(content_type or "unknown_content")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        export_dir = self.output_root / brand_key / content_key
        export_dir.mkdir(parents=True, exist_ok=True)

        exported_paths: dict[str, str] = {}
        base_name = f"{timestamp}_{content_key}"

        if "markdown" in formats:
            markdown_path = self._unique_path(export_dir / f"{base_name}.md")
            markdown_content = self.renderer.render_markdown(output, content_key)
            markdown_path.write_text(markdown_content, encoding="utf-8")
            exported_paths["markdown"] = str(markdown_path)

        if "json" in formats:
            json_path = self._unique_path(export_dir / f"{base_name}.json")
            json_payload = self._build_export_json(output, metadata, validation_result)
            json_path.write_text(json.dumps(json_payload, indent=2, ensure_ascii=False), encoding="utf-8")
            exported_paths["json"] = str(json_path)

        return exported_paths

    def build_export_summary(
        self,
        brand: str,
        content_type: str,
        exported_paths: dict[str, str],
        metadata: dict[str, Any],
        validation_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build a safe export summary for reporting."""

        return {
            "brand": normalize_key(brand or "unknown_brand"),
            "content_type": normalize_key(content_type or "unknown_content"),
            "export_count": len(exported_paths),
            "export_formats": list(exported_paths.keys()),
            "exported_paths": dict(exported_paths),
            "validation_status": str(validation_result.get("valid", False)),
            "metadata": {
                "brand": metadata.get("brand", ""),
                "platform": metadata.get("platform", ""),
                "content_type": metadata.get("content_type", ""),
                "objective": metadata.get("objective", ""),
                "audience": metadata.get("audience", ""),
                "location": metadata.get("location", ""),
                "property_type": metadata.get("property_type", ""),
            },
        }

    def _build_export_json(self, output: dict[str, Any], metadata: dict[str, Any], validation_result: dict[str, Any]) -> dict[str, Any]:
        """Build a sanitized JSON export payload."""

        safe_output = self.renderer.render_json(output)
        safe_output.pop("raw_response", None)
        return {
            "output": safe_output,
            "metadata": metadata,
            "validation_result": validation_result,
        }

    def _unique_path(self, path: Path) -> Path:
        """Return a non-overwriting file path."""

        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        index = 1
        while True:
            candidate = parent / f"{stem}_{index}{suffix}"
            if not candidate.exists():
                return candidate
            index += 1
