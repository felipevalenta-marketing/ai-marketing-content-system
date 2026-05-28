"""Structured cost tracking result builders."""

from __future__ import annotations

from typing import Any

from src.reporting.report_metrics import safe_float, safe_int, safe_text, utc_now_iso


def build_success_cost_result(
    *,
    provider: str,
    model: str,
    currency: str,
    input_tokens: int,
    output_tokens: int,
    cached_input_tokens: int,
    total_tokens: int,
    input_cost: float,
    output_cost: float,
    cached_input_cost: float,
    total_cost: float,
    estimated_tokens: bool,
    estimated_cost: bool,
    pricing_found: bool,
    pricing_version: str,
    pricing_source: str,
    execution_id: str = "",
    module: str = "",
    operation: str = "",
    campaign_id: str = "",
    asset_type: str = "",
    metadata: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build a normalized success cost result."""

    return {
        "success": True,
        "provider": safe_text(provider, limit=80),
        "model": safe_text(model, limit=80),
        "currency": safe_text(currency, limit=32) or "USD",
        "input_tokens": max(0, safe_int(input_tokens, 0)),
        "output_tokens": max(0, safe_int(output_tokens, 0)),
        "cached_input_tokens": max(0, safe_int(cached_input_tokens, 0)),
        "total_tokens": max(0, safe_int(total_tokens, 0)),
        "input_cost": safe_float(input_cost, 0.0),
        "output_cost": safe_float(output_cost, 0.0),
        "cached_input_cost": safe_float(cached_input_cost, 0.0),
        "total_cost": safe_float(total_cost, 0.0),
        "estimated_tokens": bool(estimated_tokens),
        "estimated_cost": bool(estimated_cost),
        "pricing_found": bool(pricing_found),
        "pricing_version": safe_text(pricing_version, limit=80),
        "pricing_source": safe_text(pricing_source, limit=80),
        "execution_id": safe_text(execution_id, limit=120),
        "module": safe_text(module, limit=120),
        "operation": safe_text(operation, limit=120),
        "campaign_id": safe_text(campaign_id, limit=120),
        "asset_type": safe_text(asset_type, limit=120),
        "metadata": metadata or {},
        "warnings": warnings or [],
        "errors": errors or [],
        "timestamp": utc_now_iso(),
    }


def build_unknown_pricing_result(
    *,
    provider: str = "",
    model: str = "",
    currency: str = "USD",
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_input_tokens: int = 0,
    total_tokens: int = 0,
    execution_id: str = "",
    module: str = "",
    operation: str = "",
    campaign_id: str = "",
    asset_type: str = "",
    metadata: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build a result when pricing is unknown."""

    warnings_list = list(warnings or [])
    if "Pricing not found for provider/model." not in warnings_list:
        warnings_list.append("Pricing not found for provider/model.")
    return build_success_cost_result(
        provider=provider,
        model=model,
        currency=currency,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_input_tokens=cached_input_tokens,
        total_tokens=total_tokens,
        input_cost=0.0,
        output_cost=0.0,
        cached_input_cost=0.0,
        total_cost=0.0,
        estimated_tokens=True,
        estimated_cost=True,
        pricing_found=False,
        pricing_version="unknown",
        pricing_source="unknown",
        execution_id=execution_id,
        module=module,
        operation=operation,
        campaign_id=campaign_id,
        asset_type=asset_type,
        metadata=metadata,
        warnings=warnings_list,
        errors=errors,
    )


def build_failure_cost_result(
    *,
    provider: str = "",
    model: str = "",
    execution_id: str = "",
    module: str = "",
    operation: str = "",
    campaign_id: str = "",
    asset_type: str = "",
    metadata: dict[str, Any] | None = None,
    error: str = "Cost tracking failed.",
) -> dict[str, Any]:
    """Build a structured failure result."""

    return build_success_cost_result(
        provider=provider,
        model=model,
        currency="USD",
        input_tokens=0,
        output_tokens=0,
        cached_input_tokens=0,
        total_tokens=0,
        input_cost=0.0,
        output_cost=0.0,
        cached_input_cost=0.0,
        total_cost=0.0,
        estimated_tokens=True,
        estimated_cost=True,
        pricing_found=False,
        pricing_version="unknown",
        pricing_source="unknown",
        execution_id=execution_id,
        module=module,
        operation=operation,
        campaign_id=campaign_id,
        asset_type=asset_type,
        metadata=metadata,
        warnings=[],
        errors=[error],
    )


def build_aggregation_result(summary: dict[str, Any], warnings: list[str] | None = None, errors: list[str] | None = None) -> dict[str, Any]:
    """Build an aggregation result wrapper."""

    return {
        "success": True,
        "summary": summary,
        "warnings": warnings or [],
        "errors": errors or [],
    }


def build_cost_summary_result(summary: dict[str, Any], warnings: list[str] | None = None, errors: list[str] | None = None) -> dict[str, Any]:
    """Build a structured cost summary result."""

    return {
        "success": True,
        "summary": summary,
        "warnings": warnings or [],
        "errors": errors or [],
    }
