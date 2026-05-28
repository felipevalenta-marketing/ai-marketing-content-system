"""Structured result helpers for platform adaptation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AdaptationResult:
    """Container for multi-platform adaptation outputs."""

    success: bool
    source_content_type: str
    platform_variants: dict[str, dict[str, Any]]
    warnings: list[str]
    metadata: dict[str, Any]
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the adaptation result."""

        return {
            "success": self.success,
            "source_content_type": self.source_content_type,
            "platform_variants": self.platform_variants,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "errors": self.errors,
        }


def build_adaptation_success(
    source_content_type: str,
    platform_variants: dict[str, dict[str, Any]],
    warnings: list[str],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build a successful adaptation payload."""

    return AdaptationResult(
        success=True,
        source_content_type=source_content_type,
        platform_variants=platform_variants,
        warnings=warnings,
        metadata=metadata,
        errors=[],
    ).to_dict()


def build_adaptation_failure(
    source_content_type: str,
    warnings: list[str],
    metadata: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    """Build a failed adaptation payload."""

    return AdaptationResult(
        success=False,
        source_content_type=source_content_type,
        platform_variants={},
        warnings=warnings,
        metadata=metadata,
        errors=errors,
    ).to_dict()
