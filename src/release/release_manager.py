"""Release orchestration manager."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .mvp_acceptance import build_mvp_acceptance
from .mvp_certification import build_final_mvp_declaration, build_mvp_certification
from .mvp_maturity import build_mvp_maturity
from .release_auditor import build_release_audit
from .release_checklist import build_release_checklist
from .release_governance import build_release_governance
from .release_health import build_release_health
from .release_report_builder import build_executive_summary, build_release_artifact_index, write_executive_summary, write_release_artifact_index, write_release_report
from .release_score import calculate_release_score
from .release_validator import validate_release


class ReleaseManager:
    def validate_release(self, app: Any | None = None, root: Path | None = None) -> dict[str, Any]:
        return validate_release(app=app, root=root)

    def build_release_summary(self, app: Any | None = None, root: Path | None = None) -> dict[str, Any]:
        validation = self.validate_release(app=app, root=root)
        score = calculate_release_score(validation)
        maturity = build_mvp_maturity(validation)
        governance = build_release_governance(validation)
        health = build_release_health(app=app, summary=validation)
        checklist = build_release_checklist(validation)
        audit = build_release_audit(app=app, root=root)
        certification = build_mvp_certification(app=app, root=root, summary={**validation, **score, "maturity": maturity, "governance": governance})
        acceptance = build_mvp_acceptance(app=app, root=root, summary={**validation, **score, "maturity": maturity, "governance": governance})
        final_declaration = build_final_mvp_declaration(app=app, root=root, summary={**validation, **score, "maturity": maturity, "governance": governance})
        executive_summary = build_executive_summary({**validation, **score, "maturity": maturity, "governance": governance, "certification": certification, "declaration": final_declaration}, root=root)
        artifact_index = build_release_artifact_index(root=root)
        summary = {
            **validation,
            **score,
            "maturity": maturity,
            "governance": governance,
            "release_health": health,
            "release_checklist": checklist,
            "release_audit": audit,
            "certification": certification,
            "mvp_acceptance": acceptance,
            "executive_summary": executive_summary,
            "release_artifacts": artifact_index,
            "final_mvp_declaration": final_declaration,
            "mvp_ready": bool(final_declaration.get("mvp_complete", False)),
            "release_ready": bool(validation.get("release_ready", False)),
            "production_ready": bool(final_declaration.get("production_ready", False)),
            "version": final_declaration.get("version", acceptance.get("version", "1.0.0")),
            "readiness_status": str(final_declaration.get("release_status", score.get("release_status", "blocked"))),
            "certification_status": str(certification.get("certification_status", "blocked")),
            "maturity_level": str(maturity.get("maturity_level", "prototype")),
            "maturity_score": int(maturity.get("maturity_score", 0)),
            "overall_score": int(score.get("overall_score", score.get("release_score", 0))),
        }
        return summary

    def generate_release_package(self, app: Any | None = None, root: Path | None = None) -> dict[str, Any]:
        summary = self.build_release_summary(app=app, root=root)
        report = self.generate_release_report(summary, root=root)
        return {
            "success": True,
            "summary": summary,
            "report": report,
        }

    def generate_release_report(self, summary: dict[str, Any] | None = None, root: Path | None = None) -> dict[str, Any]:
        report = write_release_report(summary or {}, root=root)
        write_executive_summary(summary or {}, root=root)
        write_release_artifact_index(root=root)
        return report
