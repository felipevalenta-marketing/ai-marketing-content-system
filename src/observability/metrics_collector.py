"""Metrics collection helpers."""

from __future__ import annotations

from typing import Any

from .metrics_registry import get_metrics_registry


def collect_metrics() -> dict[str, Any]:
    metrics = get_metrics_registry().get_metrics()
    metrics.setdefault("success", True)
    return metrics
