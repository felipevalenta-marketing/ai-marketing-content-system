from __future__ import annotations

from pathlib import Path

from scripts.ci_security_check import scan_repository


def test_security_scan_ignores_env_example_placeholders(tmp_path: Path) -> None:
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


def test_security_scan_detects_committed_env_file(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("OPENAI_API_KEY=test", encoding="utf-8")
    result = scan_repository(tmp_path)
    assert result["success"] is False
    assert any("Committed .env file" in error for error in result["errors"])


def test_security_scan_detects_obvious_sk_key(tmp_path: Path) -> None:
    secret_value = "-".join(["sk", "1234567890abcdef123456"])
    (tmp_path / "sample.txt").write_text(secret_value, encoding="utf-8")
    result = scan_repository(tmp_path)
    assert result["success"] is False
    assert any("OpenAI-style secret key" in error for error in result["errors"])


def test_security_scan_detects_hygiene_and_artifact_issues(tmp_path: Path, monkeypatch) -> None:
    from scripts import ci_security_check

    tracked_env = tmp_path / ".env.local"
    tracked_env.write_text("OPENAI_API_KEY=test", encoding="utf-8")
    pycache_file = tmp_path / "__pycache__" / "bad.pyc"
    pycache_file.parent.mkdir(parents=True, exist_ok=True)
    pycache_file.write_bytes(b"pyc")
    temp_file = tmp_path / "scratch.tmp"
    temp_file.write_text("temp", encoding="utf-8")
    big_file = tmp_path / "large.bin"
    big_file.write_bytes(b"0" * (50 * 1024 * 1024 + 1))
    artifact_file = tmp_path / "outputs" / "artifact.txt"
    artifact_file.parent.mkdir(parents=True, exist_ok=True)
    artifact_file.write_text("OPENAI_API_KEY=sk-1234567890abcdef123456", encoding="utf-8")

    monkeypatch.setattr(ci_security_check, "_tracked_files", lambda root: [tracked_env, pycache_file, temp_file, big_file])
    monkeypatch.setattr(ci_security_check, "_artifact_files", lambda root: [artifact_file])

    result = scan_repository(tmp_path)

    assert result["success"] is False
    assert any("Suspicious env file" in error for error in result["errors"])
    assert any("Compiled cache file" in error for error in result["errors"])
    assert any("Temporary file" in error for error in result["errors"])
    assert any("Large binary file" in error for error in result["errors"])
    assert any("secret" in error.lower() for error in result["errors"])
