"""Dict-friendly security contracts."""

from __future__ import annotations

from typing import Any


def build_security_summary_contract() -> dict[str, Any]:
    return {
        "security_score": 0,
        "security_status": "critical",
        "security_ready": False,
        "release_ready": False,
        "active_protections": {},
        "findings": [],
        "dependency_report": {},
        "secret_scan_report": {},
        "warnings": [],
        "errors": [],
        "metadata": {},
    }


def build_security_score_contract() -> dict[str, Any]:
    return {"security_score": 0, "security_status": "critical", "warnings": [], "recommendations": []}


def build_security_findings_contract() -> dict[str, Any]:
    return {"findings": [], "count": 0, "warnings": [], "errors": []}


def build_dependency_report_contract() -> dict[str, Any]:
    return {"dependencies_valid": True, "warnings": [], "errors": [], "metadata": {}}


def build_secret_scan_report_contract() -> dict[str, Any]:
    return {"success": True, "scanned_files": 0, "findings": [], "warnings": [], "errors": []}


def build_api_response_contract() -> dict[str, Any]:
    return {"success": True, "data": {}, "warnings": [], "errors": [], "metadata": {}}

