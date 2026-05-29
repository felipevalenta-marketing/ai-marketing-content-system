"""Backward-compatible health monitor wrapper."""

from __future__ import annotations

from typing import Any

from .observability_health import build_observability_health


def build_health_status(app: Any | None = None) -> dict[str, Any]:
    return build_observability_health(app)


__all__ = ["build_observability_health", "build_health_status"]
