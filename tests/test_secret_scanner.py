from __future__ import annotations

from pathlib import Path

from src.security.secret_scanner import build_findings_report, scan_repository


def test_secret_scanner_ignores_env_example_placeholders(tmp_path: Path) -> None:
    (tmp_path / ".env.example").write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=your_openai_api_key_here",
                "JWT_SECRET_KEY=replace_with_secure_random_value",
                "ENABLE_AUTHENTICATION=true",
            ]
        ),
        encoding="utf-8",
    )
    result = scan_repository(tmp_path)
    assert result["success"] is True
    assert result["errors"] == []


def test_secret_scanner_detects_real_secrets(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("OPENAI_API_KEY=test", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("sk-1234567890abcdef123456", encoding="utf-8")
    result = scan_repository(tmp_path)
    assert result["success"] is False
    assert any("OPENAI_API_KEY" in error or "OpenAI-style secret key" in error for error in result["errors"])


def test_secret_scanner_builds_findings_report(tmp_path: Path) -> None:
    (tmp_path / "payload.txt").write_text("Bearer abcdefghijklmnopqrstuvwxyz123456", encoding="utf-8")
    report = build_findings_report(tmp_path)
    assert report["success"] is False
    assert report["count"] >= 1

