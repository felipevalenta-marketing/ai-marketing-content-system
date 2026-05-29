from __future__ import annotations

from pathlib import Path

from src.reports.markdown_exporter import MarkdownExporter
from src.storage.json_store import read_json


def test_markdown_exporter_writes_file(tmp_path: Path) -> None:
    exporter = MarkdownExporter(output_root=tmp_path)
    result = exporter.export_markdown(
        "# Workflow Report\n\nSafe content.",
        {"brand": "wenzel_partner", "report_type": "workflow_report", "title": "Workflow Report"},
        overwrite=False,
    )

    assert result["success"] is True
    assert Path(result["path"]).exists()


def test_markdown_exporter_uses_unique_path(tmp_path: Path) -> None:
    exporter = MarkdownExporter(output_root=tmp_path)
    first = exporter.export_markdown(
        "# Workflow Report\n\nSafe content.",
        {"brand": "wenzel_partner", "report_type": "workflow_report", "title": "Workflow Report"},
        overwrite=False,
    )
    second = exporter.export_markdown(
        "# Workflow Report\n\nSafe content.",
        {"brand": "wenzel_partner", "report_type": "workflow_report", "title": "Workflow Report"},
        overwrite=False,
    )

    assert first["path"] != second["path"]
    assert Path(first["path"]).exists()
    assert Path(second["path"]).exists()


def test_markdown_exporter_updates_index(tmp_path: Path) -> None:
    exporter = MarkdownExporter(output_root=tmp_path)
    result = exporter.export_markdown(
        "# Workflow Report\n\nSafe content.",
        {
            "brand": "wenzel_partner",
            "report_type": "workflow_report",
            "title": "Workflow Report",
            "generated_at": "2026-05-29T00:00:00+00:00",
        },
        overwrite=True,
    )

    index_path = tmp_path / "index.json"
    index_result = read_json(index_path)

    assert result["success"] is True
    assert result["index_path"] == str(index_path)
    assert result["report_id"]
    assert index_result["success"] is True
    assert index_result["record"]["records"][0]["report_id"] == result["report_id"]
