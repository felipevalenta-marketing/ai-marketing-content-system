from __future__ import annotations

from pathlib import Path

from scripts.ci_docs_check import check_documentation


def test_docs_check_passes_with_required_docs(tmp_path: Path) -> None:
    for rel in ["README.md", "deployment/README.md", "docs/CI_CD.md"]:
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("docs", encoding="utf-8")

    result = check_documentation(tmp_path)

    assert result["documentation_valid"] is True
    assert result["errors"] == []


def test_docs_check_reports_missing_docs(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")
    result = check_documentation(tmp_path)
    assert result["documentation_valid"] is False
    assert result["errors"]
