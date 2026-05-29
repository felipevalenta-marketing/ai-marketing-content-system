from __future__ import annotations

from pathlib import Path

from src.configuration.config_manager import ConfigManager
from src.configuration.feature_flags import FeatureFlagManager
from src.configuration.module_registry import build_module_registry


def test_config_manager_loads_defaults_and_updates_flags(tmp_path: Path) -> None:
    manager = ConfigManager(config_root=str(tmp_path / "config"))

    platform = manager.get_platform_config()
    features = manager.get_feature_flags()
    modules = manager.get_module_registry()
    limits = manager.get_limits()
    environment = manager.get_environment_config()
    health = manager.get_configuration_health()

    assert platform["platform_name"] == "AI Marketing Content System"
    assert features["authentication"] is True
    assert modules
    assert limits["max_users"] == 1000
    assert environment["environment"] == "development"
    assert health["valid"] is True

    update = manager.update_feature_flag("markdown_reports", False)
    assert update["success"] is True
    assert manager.get_feature_flags()["markdown_reports"] is False


def test_config_manager_env_overrides_file_config(monkeypatch, tmp_path: Path) -> None:
    config_root = tmp_path / "config"
    config_root.mkdir(parents=True, exist_ok=True)
    (config_root / "platform.json").write_text(
        "{\"platform_name\": \"File Platform\", \"maintenance_mode\": false, \"environment\": \"staging\"}",
        encoding="utf-8",
    )
    (config_root / "features.json").write_text("{\"analytics_dashboard\": false}", encoding="utf-8")
    monkeypatch.setenv("PLATFORM_NAME", "Env Platform")
    monkeypatch.setenv("ANALYTICS_DASHBOARD", "true")
    monkeypatch.setenv("MAINTENANCE_MODE", "true")

    manager = ConfigManager(config_root=str(config_root))
    platform = manager.get_platform_config()
    features = manager.get_feature_flags()

    assert platform["platform_name"] == "Env Platform"
    assert platform["maintenance_mode"] is True
    assert features["analytics_dashboard"] is True


def test_config_manager_sanitizes_secret_fields(tmp_path: Path) -> None:
    config_root = tmp_path / "config"
    config_root.mkdir(parents=True, exist_ok=True)
    (config_root / "platform.json").write_text(
        "{\"platform_name\": \"Safe Platform\", \"api_key\": \"should-not-leak\", \"password\": \"hidden\", \"provider_credentials\": \"hidden\"}",
        encoding="utf-8",
    )

    manager = ConfigManager(config_root=str(config_root))
    platform = manager.get_platform_config()

    assert platform["api_key"] == "[redacted]"
    assert platform["password"] == "[redacted]"
    assert platform["provider_credentials"] == "[redacted]"
    assert "should-not-leak" not in str(platform)


def test_config_manager_health_works_with_missing_files(tmp_path: Path) -> None:
    manager = ConfigManager(config_root=str(tmp_path / "missing-config"))
    health = manager.get_configuration_health()

    assert health["valid"] is True
    assert health["status"] in {"healthy", "warning"}


def test_feature_flag_manager_and_module_registry() -> None:
    flags = FeatureFlagManager({"alpha": True, "beta": False})
    assert flags.is_enabled("alpha") is True
    assert flags.is_disabled("beta") is True
    assert flags.list_flags() == {"alpha": True, "beta": False}
    assert any(module["module"] == "authentication" for module in build_module_registry())
