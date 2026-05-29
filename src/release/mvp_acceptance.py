"""MVP acceptance helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .mvp_certification import build_final_mvp_declaration, build_mvp_certification


def build_mvp_acceptance(app: Any | None = None, root: Path | None = None, summary: dict[str, Any] | None = None) -> dict[str, Any]:
    certification = build_mvp_certification(app=app, root=root, summary=summary)
    declaration = build_final_mvp_declaration(app=app, root=root, summary=summary)
    return {
        "mvp_ready": bool(certification.get("mvp_certified", False)),
        "release_ready": bool(certification.get("production_ready", False)),
        "version": certification.get("version", "1.0.0"),
        "acceptance_score": int(certification.get("release_score", 0)),
        "status": str(certification.get("certification_status", "blocked")),
        "certification": certification,
        "declaration": declaration,
    }
