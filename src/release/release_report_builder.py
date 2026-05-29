"""Build MVP readiness reports and release documentation."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


REPORT_PATH = Path("docs/MVP_READINESS_REPORT.md")
EXECUTIVE_SUMMARY_PATH = Path("docs/MVP_EXECUTIVE_SUMMARY.md")
ARTIFACT_INDEX_PATH = Path("docs/RELEASE_ARTIFACTS.md")


def _summary_line(summary: dict[str, Any] | None, key: str, fallback: str = "") -> str:
    value = (summary or {}).get(key, fallback)
    return str(value)


def build_release_report(summary: dict[str, Any] | None = None, *, root: Path | None = None) -> str:
    summary = dict(summary or {})
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "# MVP Readiness Report",
        "",
        f"Generated at: {generated_at}",
        "",
        "## Executive Summary",
        "",
        f"- MVP Ready: {summary.get('mvp_ready', False)}",
        f"- Release Ready: {summary.get('release_ready', False)}",
        f"- Release Score: {summary.get('release_score', 0)}",
        f"- Release Status: {_summary_line(summary, 'release_status', 'blocked')}",
        f"- Maturity Level: {_summary_line(summary.get('maturity'), 'maturity_level', summary.get('maturity_level', 'prototype'))}",
        f"- Certification Status: {_summary_line(summary.get('certification'), 'certification_status', summary.get('certification_status', 'blocked'))}",
        "",
        "## Validation Summary",
        "",
    ]
    for section in ("functional", "technical", "security", "deployment", "observability", "ci", "documentation"):
        payload = summary.get(section, {})
        if isinstance(payload, dict):
            lines.append(f"- {section.title()}: {json.dumps(payload, ensure_ascii=False, default=str)}")
    lines.extend([
        "",
        "## Recommendations",
        "",
    ])
    recommendations = summary.get("recommendations", [])
    if recommendations:
        lines.extend(f"- {item}" for item in recommendations)
    else:
        lines.append("- None")
    return "\n".join(lines).strip() + "\n"


def build_executive_summary(summary: dict[str, Any] | None = None, *, root: Path | None = None) -> str:
    summary = dict(summary or {})
    certification = summary.get("certification", {}) if isinstance(summary.get("certification"), dict) else {}
    maturity = summary.get("maturity", {}) if isinstance(summary.get("maturity"), dict) else {}
    security = summary.get("security", {}) if isinstance(summary.get("security"), dict) else {}
    deployment = summary.get("deployment", {}) if isinstance(summary.get("deployment"), dict) else {}
    recommendation = "Approved for MVP 1.0 release."
    if not bool(summary.get("production_ready", certification.get("production_ready", False))):
        recommendation = "Release is not yet approved. Review governance and readiness gaps."
    elif summary.get("warnings"):
        recommendation = "Release is approved with warnings. Review the summary before tagging."
    lines = [
        "# MVP Executive Summary",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Project Overview",
        "",
        "AI Marketing Content System MVP release readiness summary for stakeholder review.",
        "",
        "## Completed FR Roadmap",
        "",
        "- FR-001 through FR-039 complete",
        "",
        "## Release Snapshot",
        "",
        f"- Release Score: {summary.get('release_score', 0)}",
        f"- Maturity Score: {summary.get('maturity_score', maturity.get('maturity_score', 0))}",
        f"- Certification Status: {summary.get('certification_status', certification.get('certification_status', 'blocked'))}",
        f"- Release Status: {summary.get('release_status', 'blocked')}",
        f"- Maturity Level: {summary.get('maturity_level', maturity.get('maturity_level', 'prototype'))}",
        f"- Production Ready: {summary.get('production_ready', certification.get('production_ready', False))}",
        "",
        "## Readiness Highlights",
        "",
        f"- Security Ready: {security.get('security_ready', summary.get('security_ready', False))}",
        f"- Deployment Ready: {deployment.get('deployment_ready', summary.get('deployment_ready', False))}",
        f"- Observability Ready: {summary.get('observability_ready', False)}",
        f"- CI Ready: {summary.get('ci_ready', False)}",
        "",
        "## Final Recommendation",
        "",
        recommendation,
    ]
    return "\n".join(lines).strip() + "\n"


def build_release_artifact_index(*, root: Path | None = None) -> str:
    lines = [
        "# Release Artifacts",
        "",
        "Single navigation point for final MVP release documents.",
        "",
        "## Artifacts",
        "",
        "- [MVP_ACCEPTANCE.md](MVP_ACCEPTANCE.md)",
        "- [MVP_READINESS_REPORT.md](MVP_READINESS_REPORT.md)",
        "- [MVP_EXECUTIVE_SUMMARY.md](MVP_EXECUTIVE_SUMMARY.md)",
        "- [RELEASE_NOTES.md](RELEASE_NOTES.md)",
        "- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def write_release_report(summary: dict[str, Any] | None = None, *, root: Path | None = None, path: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    report_path = path or root / REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    content = build_release_report(summary, root=root)
    report_path.write_text(content, encoding="utf-8")
    return {"generated": True, "path": str(report_path), "content": content}


def write_executive_summary(summary: dict[str, Any] | None = None, *, root: Path | None = None, path: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    summary_path = path or root / EXECUTIVE_SUMMARY_PATH
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    content = build_executive_summary(summary, root=root)
    summary_path.write_text(content, encoding="utf-8")
    return {"generated": True, "path": str(summary_path), "content": content}


def write_release_artifact_index(*, root: Path | None = None, path: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    artifact_path = path or root / ARTIFACT_INDEX_PATH
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    content = build_release_artifact_index(root=root)
    artifact_path.write_text(content, encoding="utf-8")
    return {"generated": True, "path": str(artifact_path), "content": content}
