"""Security event compatibility helpers.

This module prepares a lightweight in-memory event surface for future audit
logging without persisting sensitive material.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any
import uuid

from src.observability.log_sanitizer import redact_log_payload


_RECENT_EVENTS: deque[dict[str, Any]] = deque(maxlen=200)


def build_security_event(
    *,
    event_type: str,
    severity: str = "info",
    module: str = "security",
    message: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": uuid.uuid4().hex,
        "event_type": str(event_type or "security_event"),
        "severity": str(severity or "info").lower(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": str(module or "security"),
        "message": str(message or ""),
        "metadata": redact_log_payload(dict(metadata or {})),
    }


def record_security_event(
    *,
    event_type: str,
    severity: str = "info",
    module: str = "security",
    message: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = build_security_event(event_type=event_type, severity=severity, module=module, message=message, metadata=metadata)
    _RECENT_EVENTS.appendleft(event)
    return event


def list_recent_security_events(limit: int = 20) -> list[dict[str, Any]]:
    return [dict(event) for event in list(_RECENT_EVENTS)[: max(0, int(limit or 0))]]


def build_security_event_summary(limit: int = 20) -> dict[str, Any]:
    recent = list_recent_security_events(limit=limit)
    by_severity = {"info": 0, "warning": 0, "error": 0, "critical": 0}
    for event in recent:
        severity = str(event.get("severity", "info")).lower()
        if severity not in by_severity:
            severity = "info"
        by_severity[severity] += 1
    warnings = [event.get("message", "") for event in recent if str(event.get("severity", "")).lower() == "warning"]
    return {
        "recent_events": recent,
        "recent_security_warnings": warnings,
        "total_events": len(recent),
        "by_severity": by_severity,
    }
