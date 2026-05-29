"""Module registry for platform capabilities."""

from __future__ import annotations

from typing import Any

from src.configuration.config_defaults import DEFAULT_MODULES


def build_module_registry() -> list[dict[str, Any]]:
    return [dict(item) for item in DEFAULT_MODULES]

