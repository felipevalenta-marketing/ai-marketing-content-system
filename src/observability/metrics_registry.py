"""In-memory metrics registry."""

from __future__ import annotations

from collections import defaultdict
from threading import RLock
from typing import Any


_DOMAINS = [
    "api",
    "auth",
    "rbac",
    "brands",
    "organizations",
    "workflows",
    "storage",
    "analytics",
    "tokens",
    "costs",
    "observability",
]


def _label_key(labels: dict[str, Any] | None) -> str:
    if not labels:
        return ""
    return "|".join(f"{key}={labels[key]}" for key in sorted(labels))


def _parse_label_key(label_key: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if not label_key:
        return parsed
    for item in str(label_key).split("|"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parsed[str(key)] = str(value)
    return parsed


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._counters: dict[str, dict[str, float]] = defaultdict(dict)
        self._durations: dict[str, dict[str, list[float]]] = defaultdict(dict)

    def increment_counter(self, name: str, labels: dict[str, Any] | None = None, value: float = 1.0) -> None:
        label_key = _label_key(labels)
        with self._lock:
            counters = self._counters.setdefault(name, {})
            counters[label_key] = float(counters.get(label_key, 0.0)) + float(value or 0.0)

    def record_duration(self, name: str, duration_ms: float, labels: dict[str, Any] | None = None) -> None:
        label_key = _label_key(labels)
        with self._lock:
            durations = self._durations.setdefault(name, {})
            series = durations.setdefault(label_key, [])
            series.append(max(0.0, float(duration_ms or 0.0)))

    def get_metrics(self) -> dict[str, Any]:
        with self._lock:
            summary: dict[str, Any] = {
                "total_requests": self._sum_counter("total_requests"),
                "requests_by_path": self._counter_map("requests_by_path"),
                "requests_by_status": self._counter_map("requests_by_status"),
                "error_count": self._sum_counter("error_count"),
                "average_response_time_ms": self._average_duration("request_duration_ms"),
                "workflow_runs": self._sum_counter("workflow_runs"),
                "workflow_failures": self._sum_counter("workflow_failures"),
                "storage_errors": self._sum_counter("storage_errors"),
                "token_usage_total": self._sum_counter("token_usage_total"),
                "cost_total": self._sum_counter("cost_total"),
                "auth_failures": self._sum_counter("auth_failures"),
                "durations": self._duration_summary(),
                "counters": self._copy_counters(),
                "domains": self.list_domains(),
            }
            return summary

    def reset_metrics(self) -> dict[str, Any]:
        with self._lock:
            self._counters.clear()
            self._durations.clear()
        return self.get_metrics()

    def list_domains(self) -> list[str]:
        return list(_DOMAINS)

    def get_domain_metrics(self, domain: str) -> dict[str, Any]:
        normalized = str(domain or "").strip().lower()
        summary = self.get_metrics()
        if normalized == "api":
            return {
                "domain": "api",
                "metrics": {
                    "total_requests": summary.get("total_requests", 0),
                    "requests_by_path": summary.get("requests_by_path", {}),
                    "requests_by_status": summary.get("requests_by_status", {}),
                    "error_count": summary.get("error_count", 0),
                    "average_response_time_ms": summary.get("average_response_time_ms", 0),
                },
            }
        if normalized == "auth":
            return {"domain": "auth", "metrics": {"auth_failures": summary.get("auth_failures", 0)}}
        if normalized == "rbac":
            return {"domain": "rbac", "metrics": {"auth_failures": summary.get("auth_failures", 0)}}
        if normalized == "storage":
            return {"domain": "storage", "metrics": {"storage_errors": summary.get("storage_errors", 0)}}
        if normalized == "workflows":
            from .workflow_monitor import get_workflow_monitor

            workflow_metrics = get_workflow_monitor().get_metrics()
            return {"domain": "workflows", "metrics": workflow_metrics}
        if normalized == "tokens":
            return {"domain": "tokens", "metrics": self._labeled_metrics("token_usage_total", value_name="total_tokens")}
        if normalized == "costs":
            return {"domain": "costs", "metrics": self._labeled_metrics("cost_total", value_name="total_cost")}
        if normalized == "observability":
            return {
                "domain": "observability",
                "metrics": {
                    "total_requests": summary.get("total_requests", 0),
                    "error_count": summary.get("error_count", 0),
                    "domains": self.list_domains(),
                },
            }
        return {"domain": normalized, "metrics": {}}

    def _sum_counter(self, name: str) -> float:
        return float(sum(self._counters.get(name, {}).values()))

    def _counter_map(self, name: str) -> dict[str, float]:
        return {key: float(value) for key, value in self._counters.get(name, {}).items() if key}

    def _average_duration(self, name: str) -> float:
        values = [item for series in self._durations.get(name, {}).values() for item in series]
        return round(sum(values) / len(values), 3) if values else 0.0

    def _duration_summary(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for name, series_map in self._durations.items():
            values = [item for series in series_map.values() for item in series]
            result[name] = {"count": len(values), "average": round(sum(values) / len(values), 3) if values else 0.0, "latest": round(values[-1], 3) if values else 0.0}
        return result

    def _copy_counters(self) -> dict[str, Any]:
        return {name: {key: float(value) for key, value in labels.items()} for name, labels in self._counters.items()}

    def _labeled_metrics(self, counter_name: str, *, value_name: str) -> dict[str, Any]:
        with self._lock:
            series = dict(self._counters.get(counter_name, {}))
        totals: dict[str, float] = {}
        by_workflow: dict[str, float] = {}
        by_organization: dict[str, float] = {}
        by_brand: dict[str, float] = {}
        for label_key, value in series.items():
            labels = _parse_label_key(label_key)
            total_key = labels.get("workflow_id") or labels.get("organization_id") or labels.get("brand_id") or "overall"
            totals[total_key] = float(totals.get(total_key, 0.0)) + float(value)
            if labels.get("workflow_id"):
                by_workflow[labels["workflow_id"]] = float(by_workflow.get(labels["workflow_id"], 0.0)) + float(value)
            if labels.get("organization_id"):
                by_organization[labels["organization_id"]] = float(by_organization.get(labels["organization_id"], 0.0)) + float(value)
            if labels.get("brand_id"):
                by_brand[labels["brand_id"]] = float(by_brand.get(labels["brand_id"], 0.0)) + float(value)
        metrics = {
            "total": round(sum(series.values()), 6),
            value_name: round(sum(series.values()), 6),
            "by_workflow": {key: round(value, 6) for key, value in by_workflow.items()},
            "by_organization": {key: round(value, 6) for key, value in by_organization.items()},
            "by_brand": {key: round(value, 6) for key, value in by_brand.items()},
            "by_scope": {key: round(value, 6) for key, value in totals.items()},
        }
        if value_name == "total_tokens":
            metrics["tokens_by_workflow"] = metrics["by_workflow"]
            metrics["tokens_by_organization"] = metrics["by_organization"]
            metrics["tokens_by_brand"] = metrics["by_brand"]
        else:
            metrics["cost_by_workflow"] = metrics["by_workflow"]
            metrics["cost_by_organization"] = metrics["by_organization"]
            metrics["cost_by_brand"] = metrics["by_brand"]
        return metrics



_METRICS_REGISTRY = MetricsRegistry()


def get_metrics_registry() -> MetricsRegistry:
    return _METRICS_REGISTRY
