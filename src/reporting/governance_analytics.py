"""Governance analytics for approvals and safety signals."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_bool, safe_dict, safe_float, safe_list, safe_text, unique_strings


class GovernanceAnalytics:
    """Derive governance metrics from content review payloads."""

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Analyze a governance result payload."""

        governance_result = safe_dict(payload.get("governance_result"))
        if not governance_result:
            governance_result = safe_dict(payload.get("validation_result"))
        if not governance_result:
            governance_result = safe_dict(payload.get("governance_summary"))

        warnings = unique_strings(governance_result.get("warnings") or payload.get("warnings", []))
        errors = unique_strings(governance_result.get("errors") or payload.get("errors", []))
        checks = safe_dict(governance_result.get("checks"))

        quality = safe_float(governance_result.get("quality_score"))
        brand = safe_float(governance_result.get("brand_score"))
        platform = safe_float(governance_result.get("platform_score"))
        factual = safe_float(governance_result.get("factual_safety_score"))
        overall = safe_float(governance_result.get("overall_score"))
        status = safe_text(governance_result.get("status", "unknown"), limit=80).lower() or "unknown"

        if not overall and any([quality, brand, platform, factual]):
            overall = round((quality * 0.30) + (brand * 0.25) + (platform * 0.20) + (factual * 0.25), 2)

        return {
            "approved": safe_bool(governance_result.get("approved")),
            "status": status,
            "quality_score": quality,
            "brand_score": brand,
            "platform_score": platform,
            "factual_safety_score": factual,
            "overall_score": overall,
            "warning_count": len(warnings),
            "error_count": len(errors),
            "warnings": warnings,
            "errors": errors,
            "check_count": len(checks),
            "checks": checks,
            "recommendations": safe_list(governance_result.get("recommendations")),
            "approval_signal": "approved" if safe_bool(governance_result.get("approved")) else status,
        }
