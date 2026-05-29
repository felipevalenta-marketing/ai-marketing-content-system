"""Security hardening layer for the AI Marketing Content System."""

from .security_manager import SecurityManager
from .security_config import SecurityConfig, build_security_configuration
from .security_health import build_security_baseline, build_security_health, get_system_status_summary
from .security_policy import build_security_policy, build_security_policy_summary
from .security_events import build_security_event, build_security_event_summary, list_recent_security_events, record_security_event

get_security_status_summary = get_system_status_summary

__all__ = [
    "SecurityManager",
    "SecurityConfig",
    "build_security_configuration",
    "build_security_baseline",
    "build_security_health",
    "build_security_policy",
    "build_security_policy_summary",
    "build_security_event",
    "build_security_event_summary",
    "record_security_event",
    "list_recent_security_events",
    "get_system_status_summary",
    "get_security_status_summary",
]
