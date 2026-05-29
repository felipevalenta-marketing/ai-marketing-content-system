from __future__ import annotations

import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parents[1]


def _prepare_sys_path() -> None:
    root = _root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _secret_like(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(_secret_like(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_secret_like(item) for item in value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {
            "replace_with_secure_random_value",
            "your_openai_api_key_here",
            "your_jwt_secret_key",
            "dummy_ci_key_do_not_use",
            "dummy_ci_jwt_secret_for_tests_only",
        }:
            return False
        return lowered.startswith("sk-")
    return False


def check_backend(root: Path | None = None) -> dict[str, object]:
    _prepare_sys_path()
    from fastapi.testclient import TestClient

    from src.api.api_config import ApiConfig, build_api_config_summary
    from src.api.main import create_app
    from src.api.health import build_health_payload

    app = create_app(ApiConfig())
    client = TestClient(app)
    config_summary = build_api_config_summary()

    modules_to_import = [
        "src.auth.auth_manager",
        "src.rbac.rbac_manager",
        "src.configuration.config_manager",
        "src.observability.observability_health",
        "src.analytics.analytics_engine",
        "src.reporting.reporting_engine",
        "src.organizations.organization_manager",
    ]
    import_results: dict[str, bool] = {}
    for module_name in modules_to_import:
        __import__(module_name)
        import_results[module_name] = True

    health_payload = build_health_payload(app.state.config)
    health_response = client.get("/health")
    readiness_response = client.get("/health/ready")
    liveness_response = client.get("/health/live")

    return {
        "success": bool(health_response.status_code == 200 and health_response.json().get("success")),
        "environment": health_payload.get("environment"),
        "health_status": health_payload.get("status"),
        "imports": import_results,
        "health_endpoint_ok": health_response.status_code == 200,
        "readiness_endpoint_ok": readiness_response.status_code == 200,
        "liveness_endpoint_ok": liveness_response.status_code == 200,
        "config_secrets_exposed": _secret_like(config_summary),
        "warnings": [],
        "errors": [],
    }


def main() -> int:
    result = check_backend()
    print(json.dumps(result, indent=2))
    errors = list(result.get("errors", []))
    if not result.get("health_endpoint_ok"):
        errors.append("Health endpoint failed.")
    if not result.get("readiness_endpoint_ok"):
        errors.append("Readiness endpoint failed.")
    if not result.get("liveness_endpoint_ok"):
        errors.append("Liveness endpoint failed.")
    if result.get("config_secrets_exposed"):
        errors.append("Config summary exposed secret-like values.")
    return 1 if errors or not result.get("success") else 0


if __name__ == "__main__":
    raise SystemExit(main())
