"""Logging configuration for observability events."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from .log_sanitizer import redact_log_payload


class ObservabilityFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any]
        if isinstance(record.msg, dict):
            payload = dict(record.msg)
        else:
            payload = {
                "event": record.getMessage(),
                "module": record.name,
            }
        payload.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        payload.setdefault("level", record.levelname.lower())
        payload.setdefault("module", record.name)
        sanitized = redact_log_payload(payload)
        return json.dumps(sanitized, ensure_ascii=False, default=str)


def _level_from_env() -> int:
    level_name = (os.getenv("OBSERVABILITY_LOG_LEVEL") or os.getenv("LOG_LEVEL") or "info").strip().lower()
    return {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }.get(level_name, logging.INFO)


def configure_logging(level: int | None = None) -> logging.Logger:
    logger = logging.getLogger("amcs.observability")
    logger.setLevel(level if level is not None else _level_from_env())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ObservabilityFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger
