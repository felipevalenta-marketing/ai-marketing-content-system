"""Centralized feature flag management."""

from __future__ import annotations

from typing import Any

from src.configuration.config_defaults import DEFAULT_FEATURE_FLAGS


class FeatureFlagManager:
    def __init__(self, flags: dict[str, Any] | None = None) -> None:
        self._flags = {str(key): bool(value) for key, value in dict(flags or DEFAULT_FEATURE_FLAGS).items()}

    def is_enabled(self, flag: str) -> bool:
        return bool(self._flags.get(str(flag), False))

    def is_disabled(self, flag: str) -> bool:
        return not self.is_enabled(flag)

    def list_flags(self) -> dict[str, bool]:
        return dict(self._flags)

    def update(self, flag: str, enabled: bool) -> None:
        self._flags[str(flag)] = bool(enabled)

