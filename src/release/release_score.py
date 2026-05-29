"""Release scoring helpers."""

from __future__ import annotations

from typing import Any

from .release_validator import get_domain_status, list_domains


def _factor_status(value: Any) -> bool:
    if isinstance(value, dict):
        if "ready" in value:
            return bool(value.get("ready"))
        if "valid" in value:
            return bool(value.get("valid"))
        if "passed" in value:
            return bool(value.get("passed"))
    return bool(value)


def _domain_score(domain: str, summary: dict[str, Any]) -> int:
    status = get_domain_status(domain, summary=summary)
    return 100 if status.get("status") == "pass" else 0


def calculate_release_score(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = dict(summary or {})
    factors = {
        "functionality": _factor_status(summary.get("functional_ready")),
        "testing": _factor_status(summary.get("technical_ready")),
        "security": _factor_status(summary.get("security_ready")),
        "deployment": _factor_status(summary.get("deployment_ready")),
        "observability": _factor_status(summary.get("observability_ready")),
        "documentation": _factor_status(summary.get("documentation_ready")),
        "ci_cd": _factor_status(summary.get("ci_ready")),
    }
    weights = {
        "functionality": 20,
        "testing": 15,
        "security": 20,
        "deployment": 10,
        "observability": 10,
        "documentation": 15,
        "ci_cd": 10,
    }
    domain_scores = {domain: _domain_score(domain, summary) for domain in list_domains()}
    score = 100
    for name, passed in factors.items():
        if not passed:
            score -= weights[name]
    score = max(0, min(100, score))
    domain_average_score = int(round(sum(domain_scores.values()) / max(1, len(domain_scores))))
    if score >= 95 and all(factors.values()):
        status = "ready"
    elif score >= 75:
        status = "warning"
    else:
        status = "blocked"
    recommendations = []
    if not factors["security"]:
        recommendations.append("Resolve security validations.")
    if not factors["deployment"]:
        recommendations.append("Verify deployment prerequisites.")
    if not factors["ci_cd"]:
        recommendations.append("Confirm CI quality gates pass.")
    return {
        "overall_score": score,
        "release_score": score,
        "release_status": status,
        "recommendations": recommendations,
        "factors": factors,
        "domain_scores": domain_scores,
        "domain_average_score": domain_average_score,
    }
