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
        token_usage = safe_dict(payload.get("token_usage"))
        execution_token_summary = safe_dict(payload.get("execution_token_summary"))
        module_token_summary = safe_dict(payload.get("module_token_summary"))
        provider_token_summary = safe_dict(payload.get("provider_token_summary"))
        estimated_token_usage = safe_dict(payload.get("estimated_token_usage"))
        cost_usage = safe_dict(payload.get("cost_usage"))
        execution_cost_summary = safe_dict(payload.get("execution_cost_summary"))
        module_cost_summary = safe_dict(payload.get("module_cost_summary"))
        provider_cost_summary = safe_dict(payload.get("provider_cost_summary"))
        model_cost_summary = safe_dict(payload.get("model_cost_summary"))
        persistence_result = safe_dict(payload.get("persistence_result"))
        storage_paths = safe_dict(payload.get("storage_paths"))
        stored_record_ids = safe_list(payload.get("stored_record_ids"))
        storage_warnings = safe_list(payload.get("storage_warnings"))
        storage_errors = safe_list(payload.get("storage_errors"))
        persistence_summary = {
            "records_saved": safe_int(persistence_result.get("records_saved"), 0),
            "storage_root": safe_text(persistence_result.get("storage_root"), limit=120),
            "stored_record_ids": stored_record_ids,
            "storage_paths": storage_paths,
            "markdown_saved": safe_bool(persistence_result.get("markdown_saved")),
            "persistence_status": safe_text(persistence_result.get("persistence_status"), limit=80),
            "persistence_enabled": safe_bool(persistence_result.get("enabled")),
            "persistence_success": safe_bool(persistence_result.get("success")),
        }

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
            "input_tokens": safe_int(token_usage.get("input_tokens"), 0),
            "output_tokens": safe_int(token_usage.get("output_tokens"), 0),
            "total_tokens": safe_int(token_usage.get("total_tokens"), 0),
            "estimated_usage": safe_bool(token_usage.get("estimated")),
            "token_source": safe_text(token_usage.get("source"), limit=80),
            "token_provider": safe_text(token_usage.get("provider"), limit=80),
            "token_model": safe_text(token_usage.get("model"), limit=80),
            "module_breakdown": module_token_summary.get("summary", {}) if isinstance(module_token_summary.get("summary"), dict) else {},
            "provider_breakdown": provider_token_summary.get("summary", {}) if isinstance(provider_token_summary.get("summary"), dict) else {},
            "execution_breakdown": execution_token_summary.get("summary", {}) if isinstance(execution_token_summary.get("summary"), dict) else {},
            "estimated_token_usage": estimated_token_usage,
            "input_cost": safe_float(cost_usage.get("input_cost"), 0.0),
            "output_cost": safe_float(cost_usage.get("output_cost"), 0.0),
            "cached_input_cost": safe_float(cost_usage.get("cached_input_cost"), 0.0),
            "total_cost": safe_float(cost_usage.get("total_cost"), 0.0),
            "currency": safe_text(cost_usage.get("currency"), limit=32),
            "estimated_cost": safe_bool(cost_usage.get("estimated_cost")),
            "pricing_found": safe_bool(cost_usage.get("pricing_found")),
            "pricing_version": safe_text(cost_usage.get("pricing_version"), limit=80),
            "pricing_source": safe_text(cost_usage.get("pricing_source"), limit=80),
            "cost_provider": safe_text(cost_usage.get("provider"), limit=80),
            "cost_model": safe_text(cost_usage.get("model"), limit=80),
            "module_cost_breakdown": module_cost_summary.get("summary", {}) if isinstance(module_cost_summary.get("summary"), dict) else {},
            "provider_cost_breakdown": provider_cost_summary.get("summary", {}) if isinstance(provider_cost_summary.get("summary"), dict) else {},
            "model_cost_breakdown": model_cost_summary.get("summary", {}) if isinstance(model_cost_summary.get("summary"), dict) else {},
            "execution_cost_breakdown": execution_cost_summary.get("summary", {}) if isinstance(execution_cost_summary.get("summary"), dict) else {},
            "persistence_summary": persistence_summary,
            "persistence_status": persistence_summary["persistence_status"],
            "persistence_enabled": persistence_summary["persistence_enabled"],
            "persistence_records_saved": persistence_summary["records_saved"],
            "persistence_markdown_saved": persistence_summary["markdown_saved"],
            "storage_root": persistence_summary["storage_root"],
            "storage_paths": storage_paths,
            "stored_record_ids": stored_record_ids,
            "storage_warning_count": len(storage_warnings),
            "storage_error_count": len(storage_errors),
        }
