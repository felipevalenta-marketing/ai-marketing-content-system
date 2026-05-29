from __future__ import annotations

from src.api.api_config import ApiConfig, build_api_config_summary
from src.pipeline.pipeline_config import PipelineConfig
from scripts.production_smoke import main as production_smoke_main


def test_deployment_config_reads_environment_overrides(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("API_HOST", "0.0.0.0")
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("ENABLE_CI_SECURITY_CHECKS", "true")
    monkeypatch.setenv("ENABLE_RELEASE_VALIDATION", "true")
    monkeypatch.setenv("ENABLE_DOCKER_VALIDATION", "true")

    pipeline = PipelineConfig()
    api_config = ApiConfig()
    summary = build_api_config_summary()

    assert pipeline.app_env == "production"
    assert pipeline.api_host == "0.0.0.0"
    assert pipeline.api_port == 9000
    assert pipeline.cors_origins == ["http://localhost:5173", "http://localhost:3000"]
    assert pipeline.log_level == "debug"
    assert api_config.api_host == "0.0.0.0"
    assert api_config.api_port == 9000
    assert summary["api_host"] == "0.0.0.0"
    assert summary["api_port"] == 9000
    assert "cors_origins" in summary
    assert "jwt_secret_present" in summary
    assert pipeline.enable_ci_security_checks is True
    assert pipeline.enable_release_validation is True
    assert pipeline.enable_docker_validation is True
    assert summary["configuration"]["ci_configuration"]["enable_ci_security_checks"] is True


def test_production_smoke_script_runs() -> None:
    assert production_smoke_main() == 0
