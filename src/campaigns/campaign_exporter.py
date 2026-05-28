"""Export campaign packs to markdown and JSON files."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from datetime import datetime
import json

from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_warning


class CampaignExporter:
    """Write campaign packs to disk safely."""

    def __init__(self, output_root: str = "outputs", logger: Any | None = None) -> None:
        self.output_root = Path(output_root)
        self.logger = logger or get_logger(self.__class__.__name__)

    def export(self, campaign_pack: dict[str, Any], brand: str, campaign_name: str) -> dict[str, str]:
        """Export a campaign pack to markdown and JSON files."""

        brand_key = normalize_key(brand or "unknown_brand")
        campaign_key = normalize_key(campaign_name or "campaign_pack")
        export_dir = self.output_root / brand_key / "campaigns" / campaign_key
        export_dir.mkdir(parents=True, exist_ok=True)
        export_paths: dict[str, str] = {}

        try:
            summary_path = self._unique_path(export_dir / "campaign_summary.md")
            summary_path.write_text(self._build_summary_markdown(campaign_pack), encoding="utf-8")
            export_paths["campaign_summary.md"] = str(summary_path)

            plan_path = self._unique_path(export_dir / "campaign_plan.json")
            plan_path.write_text(json.dumps(campaign_pack.get("strategy", {}), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            export_paths["campaign_plan.json"] = str(plan_path)

            assets_md_path = self._unique_path(export_dir / "assets.md")
            assets_md_path.write_text(self._build_assets_markdown(campaign_pack), encoding="utf-8")
            export_paths["assets.md"] = str(assets_md_path)

            assets_json_path = self._unique_path(export_dir / "assets.json")
            assets_json_path.write_text(json.dumps(campaign_pack.get("assets", {}), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            export_paths["assets.json"] = str(assets_json_path)

            governance_path = self._unique_path(export_dir / "governance_summary.json")
            governance_path.write_text(json.dumps(campaign_pack.get("governance_summary", {}), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
            export_paths["governance_summary.json"] = str(governance_path)
        except Exception as exc:  # pragma: no cover - defensive fallback
            log_warning(self.logger, f"Campaign export failed: {exc}")
        return export_paths

    def _build_summary_markdown(self, campaign_pack: dict[str, Any]) -> str:
        lines = [
            f"# {campaign_pack.get('campaign_name', 'Campaign Pack')}",
            "",
            f"- **Campaign Type**: {campaign_pack.get('campaign_type', '')}",
            f"- **Brand**: {campaign_pack.get('brand', '')}",
            f"- **Objective**: {campaign_pack.get('objective', '')}",
            f"- **Audience**: {campaign_pack.get('audience', '')}",
            f"- **Location**: {campaign_pack.get('location', '')}",
            f"- **Approval Status**: {campaign_pack.get('governance_summary', {}).get('status', '')}",
        ]
        if campaign_pack.get("warnings"):
            lines.extend(["", "## Warnings"])
            lines.extend([f"- {warning}" for warning in campaign_pack.get("warnings", [])])
        if campaign_pack.get("errors"):
            lines.extend(["", "## Errors"])
            lines.extend([f"- {error}" for error in campaign_pack.get("errors", [])])
        return "\n".join(lines).strip()

    def _build_assets_markdown(self, campaign_pack: dict[str, Any]) -> str:
        lines = ["# Campaign Assets", ""]
        for asset_key, asset_value in (campaign_pack.get("assets", {}) or {}).items():
            lines.append(f"## {asset_key}")
            lines.append(f"- Status: {asset_value.get('status', '')}")
            lines.append(f"- Platform: {asset_value.get('platform', '')}")
            lines.append(f"- Purpose: {asset_value.get('purpose', '')}")
            lines.append("")
        return "\n".join(lines).strip()

    def _unique_path(self, path: Path) -> Path:
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
