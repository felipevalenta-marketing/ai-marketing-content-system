"""Release governance helpers."""

from __future__ import annotations

from typing import Any

from .release_score import calculate_release_score


def build_release_governance(summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = dict(summary or {})
    score = calculate_release_score(summary)
    warnings: list[str] = []
    blocked_reasons: list[str] = []
    if not bool(summary.get("security_ready", False)):
        blocked_reasons.append("Security readiness is required for release approval.")
    if not bool(summary.get("deployment_ready", False)):
        blocked_reasons.append("Deployment readiness is required for release approval.")
    if not bool(summary.get("ci_ready", False)):
        blocked_reasons.append("CI/CD readiness is required for release approval.")
    if not bool(summary.get("documentation_ready", False)):
        warnings.append("Documentation is incomplete.")
    if int(score.get("release_score", 0)) < 95:
        warnings.append("Readiness score is below the preferred release threshold.")
    if blocked_reasons:
        governance_status = "blocked"
    elif warnings:
        governance_status = "warning"
    else:
        governance_status = "approved"
    return {
        "governance_status": governance_status,
        "release_blocked": governance_status == "blocked",
        "release_warning": governance_status == "warning",
        "approval_recommended": governance_status == "approved",
        "warnings": warnings,
        "blocked_reasons": blocked_reasons,
        "rules": {
            "security_ready_required": True,
            "deployment_ready_required": True,
            "ci_ready_required": True,
            "documentation_warning_threshold": True,
            "readiness_score_threshold": 95,
        },
    }
