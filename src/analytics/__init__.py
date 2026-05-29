"""Analytics and executive dashboard layer."""

from src.analytics.analytics_engine import AnalyticsEngine
from src.analytics.analytics_result import (
    build_dashboard_payload_result,
    build_empty_result,
    build_failure_result,
    build_success_result,
)

__all__ = [
    "AnalyticsEngine",
    "build_dashboard_payload_result",
    "build_empty_result",
    "build_failure_result",
    "build_success_result",
]
