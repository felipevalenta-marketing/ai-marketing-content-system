"""Runtime helpers shared by API routes."""

from __future__ import annotations

from typing import Any


def get_services(request: Any) -> dict[str, Any]:
    app = getattr(request, "app", None)
    state = getattr(app, "state", None)
    services = getattr(state, "services", {}) if state is not None else {}
    return services if isinstance(services, dict) else {}


def get_service(request: Any, name: str, default: Any = None) -> Any:
    return get_services(request).get(name, default)
