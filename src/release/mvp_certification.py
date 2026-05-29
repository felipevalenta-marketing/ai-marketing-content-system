"""Final MVP certification helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .mvp_maturity import build_mvp_maturity
from .release_governance import build_release_governance
from .release_score import calculate_release_score
from .release_validator import validate_release


def _root(root: Path | None = None) -> Path:
    return root or Path(__file__).resolve().parents[2]


def _resolve_summary(app: Any | None = None, root: Path | None = None, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(summary, dict) and summary:
        return dict(summary)
    return validate_release(app=app, root=root)


def build_mvp_certification(app: Any | None = None, root: Path | None = None, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    release_summary = _resolve_summary(app=app, root=root, summary=summary)
    score = calculate_release_score(release_summary)
    maturity = release_summary.get("maturity") if isinstance(release_summary.get("maturity"), dict) else build_mvp_maturity(release_summary)
    governance = release_summary.get("governance") if isinstance(release_summary.get("governance"), dict) else build_release_governance(release_summary)

    release_ready = bool(release_summary.get("release_ready", False))
    security_ready = bool(release_summary.get("security_ready", False))
    deployment_ready = bool(release_summary.get("deployment_ready", False))
    ci_ready = bool(release_summary.get("ci_ready", False))
    maturity_ready = str(maturity.get("maturity_level", "")).strip().lower() == "production_ready"
    governance_status = str(governance.get("governance_status", "blocked")).strip().lower()
    certification_ready = all([release_ready, security_ready, deployment_ready, ci_ready, maturity_ready, governance_status == "approved"])

    if governance_status == "blocked":
        certification_status = "blocked"
    elif certification_ready and score.get("release_score", 0) >= 95:
        certification_status = "approved"
    else:
        certification_status = "warning"

    production_ready = bool(certification_status == "approved")
    version = str(release_summary.get("version", "1.0.0"))
    return {
        "mvp_certified": production_ready,
        "production_ready": production_ready,
        "certification_status": certification_status,
        "version": version,
        "release_score": int(score.get("release_score", 0)),
        "release_status": str(score.get("release_status", "blocked")),
        "maturity_level": str(maturity.get("maturity_level", "prototype")),
        "maturity_score": int(maturity.get("maturity_score", 0)),
        "governance_status": governance_status,
        "warnings": list(score.get("recommendations", [])) + list(maturity.get("warnings", [])) + list(governance.get("warnings", [])),
        "errors": list(maturity.get("errors", [])) + list(governance.get("errors", [])),
        "metadata": {
            "release_ready": release_ready,
            "security_ready": security_ready,
            "deployment_ready": deployment_ready,
            "ci_ready": ci_ready,
            "maturity_ready": maturity_ready,
            "score": int(score.get("release_score", 0)),
        },
    }


def build_final_mvp_declaration(app: Any | None = None, root: Path | None = None, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    certification = build_mvp_certification(app=app, root=root, summary=summary)
    release_status = "approved" if certification.get("certification_status") == "approved" else certification.get("certification_status", "blocked")
    return {
        "mvp_complete": bool(certification.get("mvp_certified", False)),
        "version": certification.get("version", "1.0.0"),
        "release_status": release_status,
        "maturity_level": certification.get("maturity_level", "prototype"),
        "production_ready": bool(certification.get("production_ready", False)),
        "certified": bool(certification.get("mvp_certified", False)),
        "release_score": int(certification.get("release_score", 0)),
    }
