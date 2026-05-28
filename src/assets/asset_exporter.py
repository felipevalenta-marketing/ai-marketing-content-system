"""Export helpers for asset coordination bundles."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_warning


class AssetExporter:
    """Export asset plans and bundles to disk."""

    def __init__(self, output_root: str = "outputs", logger: Any | None = None) -> None:
        self.output_root = Path(output_root)
        self.logger = logger or get_logger(self.__class__.__name__)

    def export(self, asset_bundle: dict[str, Any], brand: str, campaign_type: str) -> dict[str, str]:
        """Export asset coordination artifacts."""

        brand_dir = self.output_root / normalize_key(brand or "brand")
        assets_dir = brand_dir / "assets" / normalize_key(campaign_type or "campaign")
        assets_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        paths = {
            "asset_plan.json": self._unique_path(assets_dir / "asset_plan.json", timestamp),
            "asset_requirements.json": self._unique_path(assets_dir / "asset_requirements.json", timestamp),
            "asset_bundle.json": self._unique_path(assets_dir / "asset_bundle.json", timestamp),
            "asset_summary.md": self._unique_path(assets_dir / "asset_summary.md", timestamp),
        }

        try:
            self._write_json(paths["asset_plan.json"], asset_bundle.get("asset_plan", {}))
            self._write_json(paths["asset_requirements.json"], asset_bundle.get("asset_requirements", {}))
            self._write_json(paths["asset_bundle.json"], self._sanitize_bundle(asset_bundle))
            self._write_text(paths["asset_summary.md"], self._render_summary(asset_bundle))
        except OSError as exc:
            log_warning(self.logger, f"Asset export failed: {exc}")
            return {}

        return {key: str(path) for key, path in paths.items()}

    def _unique_path(self, path: Path, timestamp: str) -> Path:
        """Return a non-overwriting export path."""

        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        return path.with_name(f"{stem}_{timestamp}{suffix}")

    def _write_json(self, path: Path, data: Any) -> None:
        """Write JSON to disk safely."""

        path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    def _write_text(self, path: Path, text: str) -> None:
        """Write markdown or text content to disk."""

        path.write_text(text, encoding="utf-8")

    def _sanitize_bundle(self, asset_bundle: dict[str, Any]) -> dict[str, Any]:
        """Remove sensitive or oversized data from export payloads."""

        return {
            "brand": asset_bundle.get("brand", ""),
            "campaign_type": asset_bundle.get("campaign_type", ""),
            "objective": asset_bundle.get("objective", ""),
            "asset_plan": asset_bundle.get("asset_plan", {}),
            "asset_requirements": asset_bundle.get("asset_requirements", {}),
            "assets": asset_bundle.get("assets", {}),
            "missing_assets": asset_bundle.get("missing_assets", []),
            "validation_result": asset_bundle.get("validation_result", {}),
            "metadata": asset_bundle.get("metadata", {}),
            "warnings": asset_bundle.get("warnings", []),
            "errors": asset_bundle.get("errors", []),
        }

    def _render_summary(self, asset_bundle: dict[str, Any]) -> str:
        """Render a human-readable markdown summary."""

        lines = [
            "# Asset Summary",
            "",
            f"- Brand: {asset_bundle.get('brand', '')}",
            f"- Campaign Type: {asset_bundle.get('campaign_type', '')}",
            f"- Objective: {asset_bundle.get('objective', '')}",
            f"- Missing Assets: {', '.join(asset_bundle.get('missing_assets', [])) or 'None'}",
            f"- Validation Valid: {bool(asset_bundle.get('validation_result', {}).get('valid', False))}",
        ]
        warnings = asset_bundle.get("warnings", [])
        errors = asset_bundle.get("errors", [])
        if warnings:
            lines.extend(["", "## Warnings", *[f"- {warning}" for warning in warnings]])
        if errors:
            lines.extend(["", "## Errors", *[f"- {error}" for error in errors]])
        return "\n".join(lines)
