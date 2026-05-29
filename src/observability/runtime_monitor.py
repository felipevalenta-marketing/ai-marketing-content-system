"""Runtime diagnostics helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from platform import platform as platform_name
import os
from sys import version as python_version
from time import perf_counter
from typing import Any

from src.cli.cli_config import build_module_presence


_START = perf_counter()


def build_runtime_diagnostics(app: Any | None = None) -> dict[str, Any]:
    from src.api.api_config import ApiConfig

    config = getattr(getattr(app, "state", None), "config", None) or ApiConfig()
    services = getattr(getattr(app, "state", None), "services", {}) if app is not None else {}
    storage = services.get("storage") if isinstance(services, dict) else None
    storage_root = Path(getattr(storage, "storage_root", "data"))
    storage_root_exists = storage_root.exists()
    storage_root_writable = False
    if storage_root_exists:
        try:
            probe = storage_root / ".observability-write-check"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            storage_root_writable = True
        except Exception:
            storage_root_writable = False
    return {
        "python_version": python_version.split()[0],
        "app_env": config.environment,
        "platform": platform_name(),
        "process_uptime_seconds": round(perf_counter() - _START, 3),
        "storage_root_exists": storage_root_exists,
        "storage_root_writable": storage_root_writable,
        "enabled_modules": build_module_presence(),
        "log_level": (os.getenv("OBSERVABILITY_LOG_LEVEL") or os.getenv("LOG_LEVEL") or "info").strip().lower(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
