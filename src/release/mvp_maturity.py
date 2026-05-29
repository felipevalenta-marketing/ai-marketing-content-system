"""MVP maturity scoring helpers."""

from __future__ import annotations

from typing import Any


def _factor_status(value: Any) -> bool:
    if isinstance(value, dict):
        if "ready" in value:
            return bool(value.get("ready"))
        if "valid" in value:
            return bool(value.get("valid"))
        if "passed" in value:
            return bool(value.get("passed"))
    return bool(value)


def build_mvp_maturity(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = dict(summary or {})
    factors = {
        "security": _factor_status(summary.get("security_ready")),
        "observability": _factor_status(summary.get("observability_ready")),
        "deployment": _factor_status(summary.get("deployment_ready")),
        "ci_cd": _factor_status(summary.get("ci_ready")),
        "documentation": _factor_status(summary.get("documentation_ready")),
        "test_coverage": _factor_status(summary.get("technical_ready")),
        "platform_completeness": _factor_status(summary.get("functional_ready")),
    }
    weights = {
        "security": 20,
        "observability": 15,
        "deployment": 15,
        "ci_cd": 15,
        "documentation": 10,
        "test_coverage": 10,
        "platform_completeness": 15,
    }
    score = 100
    for name, passed in factors.items():
        if not passed:
            score -= weights[name]
    score = max(0, min(100, score))
    if score >= 95:
        level = "production_ready"
    elif score >= 80:
        level = "beta"
    elif score >= 60:
        level = "alpha"
    else:
        level = "prototype"
    warnings = []
    recommendations = []
    if not factors["security"]:
        recommendations.append("Strengthen security readiness.")
    if not factors["observability"]:
        recommendations.append("Confirm observability health.")
    if not factors["deployment"]:
        recommendations.append("Verify deployment readiness.")
    if not factors["ci_cd"]:
        recommendations.append("Re-run CI quality gates.")
    if not factors["documentation"]:
        recommendations.append("Complete MVP documentation.")
    return {
        "maturity_score": score,
        "maturity_level": level,
        "factors": factors,
        "warnings": warnings,
        "recommendations": recommendations,
    }
