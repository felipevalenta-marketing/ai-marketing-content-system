from __future__ import annotations

from scripts.check_env import validate_environment


def test_env_validation_warns_without_secrets(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("API_PORT", "8000")

    result = validate_environment()

    assert result["success"] is True
    assert result["environment"] == "development"
    assert result["app_env_present"] is True
    assert result["openai_api_key_present"] is False
    assert result["jwt_secret_key_present"] is False
    assert result["errors"] == []
    assert any("JWT_SECRET_KEY" in warning for warning in result["warnings"])


def test_env_validation_requires_secret_in_production(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("API_PORT", "8000")

    result = validate_environment()

    assert result["success"] is False
    assert any("JWT_SECRET_KEY" in error for error in result["errors"])


def test_env_validation_rejects_placeholder_secret(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "replace_with_secure_random_value")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("API_PORT", "8000")

    result = validate_environment()

    assert result["success"] is False
    assert result["jwt_secret_key_present"] is False
    assert any("JWT_SECRET_KEY" in error for error in result["errors"])
