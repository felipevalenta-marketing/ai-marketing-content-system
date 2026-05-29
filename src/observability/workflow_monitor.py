"""Workflow observation helpers."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from threading import RLock
from typing import Any


class WorkflowMonitor:
    def __init__(self, limit: int = 100) -> None:
        self._lock = RLock()
        self._workflows: deque[dict[str, Any]] = deque(maxlen=max(1, int(limit or 100)))

    def record_workflow(self, workflow: dict[str, Any]) -> dict[str, Any]:
        observation = {
            "workflow_id": str(workflow.get("workflow_id", "")),
            "workflow_type": str(workflow.get("workflow_type", "")),
            "status": str(workflow.get("status", "unknown")),
            "started_at": str(workflow.get("started_at", "")),
            "completed_at": str(workflow.get("completed_at", "")),
            "duration_seconds": float(workflow.get("duration_seconds", 0.0) or 0.0),
            "step_count": int(workflow.get("step_count", len(workflow.get("steps", []))) or 0),
            "failed_steps": int(workflow.get("failed_steps", 0) or 0),
            "warnings_count": len(workflow.get("warnings", [])) if isinstance(workflow.get("warnings"), list) else 0,
            "errors_count": len(workflow.get("errors", [])) if isinstance(workflow.get("errors"), list) else 0,
            "organization_id": str(workflow.get("organization_id", "")),
            "team_id": str(workflow.get("team_id", "")),
            "observed_at": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._workflows.appendleft(observation)
        return observation

    def get_summary(self) -> dict[str, Any]:
        metrics = self.get_metrics()
        return {
            "workflow_runs": metrics.get("total_workflow_runs", 0),
            "workflow_failures": metrics.get("failed_workflows", 0),
            "recent_workflows": metrics.get("recent_workflows", []),
            "status_breakdown": metrics.get("status_breakdown", {}),
        }

    def get_metrics(self) -> dict[str, Any]:
        with self._lock:
            recent = list(self._workflows)
        durations = [float(item.get("duration_seconds", 0.0) or 0.0) for item in recent]
        total_runs = len(recent)
        failed_workflows = sum(1 for item in recent if item.get("status") == "failed")
        completed_workflows = sum(1 for item in recent if item.get("status") in {"success", "completed", "done"})
        success_rate = round((completed_workflows / total_runs) * 100.0, 3) if total_runs else 0.0
        failure_rate = round((failed_workflows / total_runs) * 100.0, 3) if total_runs else 0.0
        return {
            "workflow_runs": total_runs,
            "workflow_failures": failed_workflows,
            "total_workflow_runs": total_runs,
            "completed_workflows": completed_workflows,
            "failed_workflows": failed_workflows,
            "workflow_success_rate": success_rate,
            "workflow_failure_rate": failure_rate,
            "avg_workflow_duration": round(sum(durations) / len(durations), 3) if durations else 0.0,
            "max_workflow_duration": round(max(durations), 3) if durations else 0.0,
            "min_workflow_duration": round(min(durations), 3) if durations else 0.0,
            "recent_workflows": recent[:20],
            "status_breakdown": self._status_breakdown(recent),
        }

    def _status_breakdown(self, records: list[dict[str, Any]]) -> dict[str, int]:
        breakdown: dict[str, int] = {}
        for record in records:
            status = str(record.get("status", "unknown"))
            breakdown[status] = int(breakdown.get(status, 0)) + 1
        return breakdown


_WORKFLOW_MONITOR = WorkflowMonitor()


def get_workflow_monitor() -> WorkflowMonitor:
    return _WORKFLOW_MONITOR
