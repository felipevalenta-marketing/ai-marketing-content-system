"""In-memory error tracker."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import RLock
from typing import Any
import uuid

from .log_sanitizer import redact_log_payload


class ErrorTracker:
    def __init__(self, limit: int = 100) -> None:
        self._lock = RLock()
        self._limit = max(1, int(limit or 100))
        self._errors: deque[dict[str, Any]] = deque(maxlen=self._limit)

    def record_error(
        self,
        *,
        error_type: str,
        module: str,
        message: str,
        request_id: str = "",
        workflow_id: str = "",
        severity: str = "error",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized_severity = str(severity or "error").strip().lower()
        if normalized_severity not in {"info", "warning", "error", "critical"}:
            normalized_severity = "error"
        error = {
            "error_id": f"err-{uuid.uuid4().hex[:12]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type,
            "module": module,
            "message": message,
            "request_id": request_id,
            "workflow_id": workflow_id,
            "severity": normalized_severity,
            "metadata": redact_log_payload(metadata or {}),
        }
        with self._lock:
            self._errors.appendleft(error)
        return error

    def list_recent_errors(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._errors)[: max(0, int(limit or 20))]

    def summarize_errors(self) -> dict[str, Any]:
        with self._lock:
            recent = list(self._errors)
        summary: dict[str, Any] = {
            "total_errors": len(recent),
            "by_type": {},
            "by_module": {},
            "by_severity": {},
            "errors_by_severity": {"info": 0, "warning": 0, "error": 0, "critical": 0},
            "recent_critical_errors": [],
            "error_trends": {},
        }
        for error in recent:
            summary["by_type"][error["error_type"]] = int(summary["by_type"].get(error["error_type"], 0)) + 1
            summary["by_module"][error["module"]] = int(summary["by_module"].get(error["module"], 0)) + 1
            summary["by_severity"][error["severity"]] = int(summary["by_severity"].get(error["severity"], 0)) + 1
            severity = str(error.get("severity", "error")).lower()
            if severity not in summary["errors_by_severity"]:
                summary["errors_by_severity"][severity] = 0
            summary["errors_by_severity"][severity] = int(summary["errors_by_severity"].get(severity, 0)) + 1
            if severity == "critical" and len(summary["recent_critical_errors"]) < 10:
                summary["recent_critical_errors"].append(error)
            timestamp = str(error.get("timestamp", "")).split("T", 1)[0]
            if timestamp:
                summary["error_trends"][timestamp] = int(summary["error_trends"].get(timestamp, 0)) + 1
        return summary


_ERROR_TRACKER = ErrorTracker()


def get_error_tracker() -> ErrorTracker:
    return _ERROR_TRACKER
