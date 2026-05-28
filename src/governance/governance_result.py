"""Structured result helpers for governance evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GovernanceResult:
    """Structured governance decision output."""

    success: bool
    approved: bool
    status: str
    quality_score: float
    brand_score: float
    platform_score: float
    factual_safety_score: float
    overall_score: float
    warnings: list[str]
    errors: list[str]
    recommendations: list[str]
    checks: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the governance result."""

        return {
            "success": self.success,
            "approved": self.approved,
            "status": self.status,
            "quality_score": self.quality_score,
            "brand_score": self.brand_score,
            "platform_score": self.platform_score,
            "factual_safety_score": self.factual_safety_score,
            "overall_score": self.overall_score,
            "warnings": self.warnings,
            "errors": self.errors,
            "recommendations": self.recommendations,
            "checks": self.checks,
            "metadata": self.metadata,
        }


def build_governance_success(
    approved: bool,
    status: str,
    quality_score: float,
    brand_score: float,
    platform_score: float,
    factual_safety_score: float,
    overall_score: float,
    warnings: list[str],
    errors: list[str],
    recommendations: list[str],
    checks: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build a governance evaluation result."""

    return GovernanceResult(
        success=True,
        approved=approved,
        status=status,
        quality_score=quality_score,
        brand_score=brand_score,
        platform_score=platform_score,
        factual_safety_score=factual_safety_score,
        overall_score=overall_score,
        warnings=warnings,
        errors=errors,
        recommendations=recommendations,
        checks=checks,
        metadata=metadata,
    ).to_dict()


def build_governance_failure(
    status: str,
    warnings: list[str],
    errors: list[str],
    recommendations: list[str],
    checks: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    """Build a failed governance payload."""

    return GovernanceResult(
        success=False,
        approved=False,
        status=status,
        quality_score=0.0,
        brand_score=0.0,
        platform_score=0.0,
        factual_safety_score=0.0,
        overall_score=0.0,
        warnings=warnings,
        errors=errors,
        recommendations=recommendations,
        checks=checks,
        metadata=metadata,
    ).to_dict()
