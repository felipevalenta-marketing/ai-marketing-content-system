"""Structured logging helpers for observability."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import logging

from .log_config import configure_logging
from .log_sanitizer import redact_log_payload


def get_observability_logger(name: str = "amcs.observability") -> logging.Logger:
    return logging.getLogger(name)


def emit_event(
    event: str,
    *,
    module: str,
    level: str = "info",
    request_id: str = "",
    user_id: str = "",
    organization_id: str = "",
    workflow_id: str = "",
    duration_ms: float = 0.0,
    metadata: dict[str, Any] | None = None,
) -> None:
    logger = configure_logging()
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
        "module": module,
        "request_id": request_id,
        "user_id": user_id,
        "organization_id": organization_id,
        "workflow_id": workflow_id,
        "duration_ms": round(float(duration_ms or 0.0), 3),
        "metadata": redact_log_payload(metadata or {}),
    }
    logger.log(getattr(logging, level.upper(), logging.INFO), record)
