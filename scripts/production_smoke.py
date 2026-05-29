from __future__ import annotations

import json
import os
import sys
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

    app = create_app(ApiConfig())
    payload = build_health_payload(app.state.config)
    config_summary = build_api_config_summary()
    storage_root = Path(getattr(getattr(app.state, "services", {}).get("storage"), "storage_root", "data")) if isinstance(getattr(app.state, "services", {}), dict) else Path("data")
    storage_root.mkdir(parents=True, exist_ok=True)
    storage_writable = False
    try:
        probe = storage_root / ".smoke-write"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        storage_writable = True
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
        "auth_config_present": bool("jwt_secret_present" in config_summary),
        "cors_origins_loaded": bool(config_summary.get("cors_origins")),
        "config_secrets_exposed": secrets_exposed,
        "warnings": [],
        "errors": [],
    }

    try:
        client = TestClient(app)
        response = client.get("/health")
        result["health_endpoint_ok"] = bool(response.status_code == 200 and response.json().get("success"))
        result["readiness_endpoint_ok"] = bool(client.get("/health/ready").status_code == 200)
        result["liveness_endpoint_ok"] = bool(client.get("/health/live").status_code == 200)
    except Exception as exc:
        result["health_endpoint_ok"] = False
        result["readiness_endpoint_ok"] = False
        result["liveness_endpoint_ok"] = False
        result["warnings"].append(str(exc))

    if not result["storage_root_writable"]:
        result["errors"].append("Storage root is not writable.")
    if result["config_secrets_exposed"]:
        result["errors"].append("Config summary exposed secret-like values.")

    print(json.dumps(result, indent=2))
    return 0 if result.get("health_endpoint_ok") and result.get("readiness_endpoint_ok") and result.get("liveness_endpoint_ok") and not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
