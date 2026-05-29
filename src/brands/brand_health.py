"""Brand health scoring helpers."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_dict, safe_list, safe_text


def build_brand_health(profile: dict[str, Any], validation: dict[str, Any] | None = None) -> dict[str, Any]:
    validation_payload = safe_dict(validation or safe_dict(profile.get("validation")))
    warnings: list[str] = []
    score = 100

    if not profile:
        return {"health_score": 0, "health_status": "critical", "warnings": ["Brand profile unavailable."]}

    if not bool(profile.get("success", True)):
        score -= 20
    if profile.get("status") in {"invalid", "missing"} or not validation_payload.get("valid", True):
        score -= 35
    if profile.get("status") == "inactive":
        score -= 20
    if profile.get("missing_recommended_files"):
        score -= min(25, 5 * len(safe_list(profile.get("missing_recommended_files"))))
        warnings.append("Some recommended brand files are missing.")
    if not profile.get("configuration_present", False):
        score -= 10
        warnings.append("Brand configuration file is missing.")
    if not profile.get("markdown_count"):
        score -= 10
        warnings.append("Brand markdown content is limited.")
    if validation_payload.get("warnings"):
        warnings.extend(safe_text(item, limit=240) for item in safe_list(validation_payload.get("warnings")) if safe_text(item, limit=240))

    score = max(0, min(100, score))
    if score >= 80 and validation_payload.get("valid", True) and profile.get("status") == "active":
        health_status = "healthy"
    elif score >= 50:
        health_status = "warning"
    else:
        health_status = "critical"
    return {"health_score": score, "health_status": health_status, "warnings": list(dict.fromkeys([item for item in warnings if item]))}
