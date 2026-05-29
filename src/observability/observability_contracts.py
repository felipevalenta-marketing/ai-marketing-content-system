"""Dict-friendly observability contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ObservabilityHealthContract:
    status: str = "unknown"
    checks: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "checks": self.checks, "warnings": self.warnings, "errors": self.errors, "timestamp": self.timestamp}


@dataclass(slots=True)
class ObservabilityMetricContract:
    name: str
    value: Any
    labels: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "value": self.value, "labels": self.labels}


@dataclass(slots=True)
class ObservabilityErrorContract:
    error_id: str
    timestamp: str
    error_type: str
    module: str
    message: str
    request_id: str = ""
    workflow_id: str = ""
    severity: str = "error"

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp,
            "error_type": self.error_type,
            "module": self.module,
            "message": self.message,
            "request_id": self.request_id,
            "workflow_id": self.workflow_id,
            "severity": self.severity,
        }
