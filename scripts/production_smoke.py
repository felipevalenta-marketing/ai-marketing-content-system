from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from collections.abc import Mapping, Sequence


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from fastapi.testclient import TestClient
    from src.api.api_config import ApiConfig
    from src.api.api_config import build_api_config_summary
    from src.api.health import build_health_payload
    from src.api.main import create_app
    from src.observability.observability_health import build_observability_configuration, build_observability_health, get_system_status_summary
    from src.observability.metrics_registry import get_metrics_registry
    from src.observability.runtime_monitor import build_runtime_diagnostics
    from src.security.security_health import build_security_health
    from src.security.security_config import build_security_configuration

    app = create_app(ApiConfig())
    payload = build_health_payload(app.state.config)
    observability_health = build_observability_health(app)
    observability_configuration = build_observability_configuration(app)
    system_status = get_system_status_summary(app)
    runtime = build_runtime_diagnostics(app)
    security_health = build_security_health(app)
    security_configuration = build_security_configuration(app)
    metrics_snapshot = get_metrics_registry().get_metrics()
    config_summary = build_api_config_summary()
    storage_root = Path(getattr(getattr(app.state, "services", {}).get("storage"), "storage_root", "data")) if isinstance(getattr(app.state, "services", {}), dict) else Path("data")
    storage_root.mkdir(parents=True, exist_ok=True)
    storage_writable = False
    try:
        probe = storage_root / ".smoke-write"
        with tempfile.NamedTemporaryFile(mode="w", dir=storage_root, delete=False, encoding="utf-8") as handle:
            handle.write("ok")
            handle.flush()
            probe = Path(handle.name)
        probe.unlink(missing_ok=True)
        storage_writable = True
    except Exception:
        try:
            storage_writable = bool(os.access(storage_root, os.W_OK))
        except Exception:
            storage_writable = False

    forbidden_keys = {"jwt_secret_key", "openai_api_key", "password_hash", "password", "api_key"}

    def _contains_secret_like_value(value: object) -> bool:
        if isinstance(value, Mapping):
            return any(
                key.lower() in forbidden_keys or _contains_secret_like_value(item)
                for key, item in value.items()
            )
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return any(_contains_secret_like_value(item) for item in value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized.startswith("sk-") or normalized in {
                "replace_with_secure_random_value",
                "your_openai_api_key_here",
                "your_jwt_secret_key",
            }
        return False

    secrets_exposed = _contains_secret_like_value(config_summary)

    result = {
        "success": True,
        "health_status": payload.get("status"),
        "environment": payload.get("environment"),
        "storage_root": str(storage_root),
        "storage_root_writable": storage_writable,
        "auth_config_present": bool(config_summary.get("enable_authentication", False)),
        "cors_origins_loaded": bool(config_summary.get("cors_origins")),
        "config_secrets_exposed": secrets_exposed,
        "observability_import_ok": bool(observability_health.get("status")),
        "observability_config_ok": bool(observability_configuration.get("observability_enabled", True)),
        "system_status_ok": bool(system_status.get("observability")),
        "security_import_ok": bool(security_health.get("security_status")),
        "security_config_ok": bool(security_configuration.get("security_enabled", True)),
        "runtime_snapshot_ok": bool(runtime.get("python_version")),
        "metrics_snapshot_ok": isinstance(metrics_snapshot, dict),
        "warnings": [],
        "errors": [],
    }

    try:
        client = TestClient(app)
        response = client.get("/health")
        result["health_endpoint_ok"] = bool(response.status_code == 200 and response.json().get("success"))
        result["readiness_endpoint_ok"] = bool(client.get("/health/ready").status_code == 200)
        result["liveness_endpoint_ok"] = bool(client.get("/health/live").status_code == 200)
        observability_health_response = client.get("/observability/health")
        observability_status_response = client.get("/observability/status")
        observability_domains_response = client.get("/observability/domains")
        observability_tokens_response = client.get("/observability/tokens")
        observability_costs_response = client.get("/observability/costs")
        observability_configuration_response = client.get("/observability/configuration")
        observability_metrics_response = client.get("/observability/metrics")
        observability_runtime_response = client.get("/observability/runtime")
        security_status_response = client.get("/security/status")
        security_health_response = client.get("/security/health")
        security_findings_response = client.get("/security/findings")
        security_dependencies_response = client.get("/security/dependencies")
        result["observability_health_ok"] = observability_health_response.status_code in {200, 401}
        result["observability_status_ok"] = observability_status_response.status_code in {200, 401}
        result["observability_domains_ok"] = observability_domains_response.status_code in {200, 401}
        result["observability_tokens_ok"] = observability_tokens_response.status_code in {200, 401}
        result["observability_costs_ok"] = observability_costs_response.status_code in {200, 401}
        result["observability_configuration_ok"] = observability_configuration_response.status_code in {200, 401}
        result["observability_metrics_ok"] = observability_metrics_response.status_code in {200, 401}
        result["observability_runtime_ok"] = observability_runtime_response.status_code in {200, 401}
        result["security_status_ok"] = security_status_response.status_code in {200, 401}
        result["security_health_ok"] = security_health_response.status_code in {200, 401}
        result["security_findings_ok"] = security_findings_response.status_code in {200, 401}
        result["security_dependencies_ok"] = security_dependencies_response.status_code in {200, 401}
    except Exception as exc:
        result["health_endpoint_ok"] = False
        result["readiness_endpoint_ok"] = False
        result["liveness_endpoint_ok"] = False
        result["observability_health_ok"] = False
        result["observability_status_ok"] = False
        result["observability_domains_ok"] = False
        result["observability_tokens_ok"] = False
        result["observability_costs_ok"] = False
        result["observability_configuration_ok"] = False
        result["observability_metrics_ok"] = False
        result["observability_runtime_ok"] = False
        result["security_status_ok"] = False
        result["security_health_ok"] = False
        result["security_findings_ok"] = False
        result["security_dependencies_ok"] = False
        result["warnings"].append(str(exc))

    if not result["storage_root_writable"]:
        result["errors"].append("Storage root is not writable.")
    if result["config_secrets_exposed"]:
        result["errors"].append("Config summary exposed secret-like values.")

    print(json.dumps(result, indent=2))
    return 0 if result.get("health_endpoint_ok") and result.get("readiness_endpoint_ok") and result.get("liveness_endpoint_ok") and result.get("observability_health_ok") and result.get("observability_status_ok") and result.get("observability_domains_ok") and result.get("observability_tokens_ok") and result.get("observability_costs_ok") and result.get("observability_configuration_ok") and result.get("observability_metrics_ok") and result.get("observability_runtime_ok") and result.get("security_status_ok") and result.get("security_health_ok") and result.get("security_findings_ok") and result.get("security_dependencies_ok") and not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
