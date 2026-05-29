from __future__ import annotations

from src.reports.markdown_renderer import clean_markdown, render_bullets, render_code_block, render_heading, render_report, render_table


def test_markdown_renderer_renders_bullets() -> None:
    output = render_bullets(["One", {"Two": "Second"}])

    assert "- One" in output
    assert "- **Two**: Second" in output


def test_markdown_renderer_renders_table() -> None:
    output = render_table([{"field": "Value", "count": 2}])

    assert "| Field | Count |" in output
    assert "| Value | 2 |" in output


def test_markdown_renderer_renders_code_block() -> None:
    output = render_code_block("print('hello')", language="python")

    assert output.startswith("```python")
    assert output.endswith("```")


def test_markdown_renderer_cleans_whitespace() -> None:
    output = clean_markdown("Title\n\n\nBody\n")

    assert output == "Title\n\nBody"


def test_markdown_renderer_renders_report() -> None:
    output = render_report("Sample Report", [render_heading("Section"), "Content"])

    assert output.startswith("# Sample Report")
    assert "## Section" in output
    assert "Content" in output

