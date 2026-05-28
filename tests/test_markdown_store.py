"""Tests for markdown persistence helpers."""

from __future__ import annotations

from pathlib import Path

from src.storage.markdown_store import render_record_markdown, write_markdown


def test_render_record_markdown_includes_core_fields():
    markdown = render_record_markdown(
        {
            "record_type": "generation",
            "record_id": "record-1",
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "campaign_type": "property_launch",
            "execution_id": "exec-1",
            "payload": {"hello": "world"},
        }
    )
    assert "Generation" in markdown
    assert "record-1" in markdown
    assert "wenzel_partner" in markdown


def test_write_markdown_round_trip(tmp_path: Path):
    path = tmp_path / "sample.md"
    result = write_markdown(path, "# Sample\n\nContent")
    assert result["success"] is True
    assert path.read_text(encoding="utf-8").startswith("# Sample")
