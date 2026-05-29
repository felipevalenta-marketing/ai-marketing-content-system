"""Security header helpers."""

from __future__ import annotations

from typing import Any

from src.security.security_config import build_security_configuration


def build_security_headers(*, app: Any | None = None, production: bool | None = None) -> dict[str, str]:
    config = build_security_configuration(app)
    is_production = bool(production if production is not None else config.get("production_mode", False))
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": str(config.get("permissions_policy", "geolocation=(), microphone=(), camera=()")),
        "Content-Security-Policy": str(config.get("csp_policy", "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'self'")),
    }
    if is_production:
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers

