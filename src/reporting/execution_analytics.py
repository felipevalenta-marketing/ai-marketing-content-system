"""Execution analytics for pipeline and CLI operations."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import (
    count_truthy,
    safe_bool,
    safe_dict,
    safe_float,
    safe_int,
    safe_list,
    safe_text,
    unique_strings,
)


class ExecutionAnalytics:
    """Derive operational metrics from execution payloads."""

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Analyze a pipeline or CLI result payload."""

        metadata = safe_dict(payload.get("metadata"))
        execution = safe_dict(metadata.get("execution"))
        ai_response = safe_dict(payload.get("ai_response"))
        prompt_payload = safe_dict(payload.get("prompt_payload"))
        warnings = unique_strings(payload.get("warnings", []))
        errors = unique_strings(payload.get("errors", []))
        exported_files = safe_dict(payload.get("exported_files"))
        exported_files.update(safe_dict(payload.get("campaign_export_paths")))
        exported_files.update(safe_dict(payload.get("asset_export_paths")))
        exported_files.update(safe_dict(payload.get("report_export_paths")))
        stage_timings = safe_dict(execution.get("stages"))

        duration_seconds = safe_float(execution.get("duration_seconds"))
        if duration_seconds <= 0 and stage_timings:
            duration_seconds = round(sum(safe_float(value) for value in stage_timings.values()), 3)

        generation_latency = safe_float(stage_timings.get("generation"))
        governance_latency = safe_float(stage_timings.get("governance"))
        export_latency = safe_float(stage_timings.get("export"))

        stages_executed = [name for name, value in stage_timings.items() if safe_float(value) >= 0.0]
        if not stages_executed and safe_dict(payload.get("summary")):
            stages_executed = ["summary"]

        return {
            "execution_time_seconds": round(duration_seconds, 3),
            "generation_latency_seconds": round(generation_latency, 3),
            "governance_latency_seconds": round(governance_latency, 3),
            "export_latency_seconds": round(export_latency, 3),
            "dry_run": safe_bool(metadata.get("dry_run")),
            "success": safe_bool(payload.get("success")),
            "warning_count": len(warnings),
            "error_count": len(errors),
            "stage_count": len(stages_executed),
            "stages_executed": stages_executed,
            "provider": safe_text(metadata.get("provider") or ai_response.get("provider") or "", limit=80),
            "model": safe_text(metadata.get("model") or ai_response.get("model") or "", limit=80),
            "content_type": safe_text(payload.get("content_type") or metadata.get("content_type") or "", limit=80),
            "brand": safe_text(payload.get("brand") or metadata.get("brand") or "", limit=80),
            "platform": safe_text(payload.get("platform") or metadata.get("platform") or "", limit=80),
            "estimated_tokens": safe_int(metadata.get("estimated_tokens"), 0) or safe_int(prompt_payload.get("estimated_tokens"), 0),
            "cost_estimate": metadata.get("cost_estimate"),
            "exported": bool(exported_files),
            "export_count": len(exported_files),
            "input_fields_present": count_truthy([payload.get("brand"), payload.get("platform"), payload.get("content_type")]),
        }
