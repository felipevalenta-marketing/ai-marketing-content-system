"""Structured token tracking result builders."""

from __future__ import annotations

from typing import Any

from src.tracking.token_usage import TokenUsage


def build_success_usage_result(
    *,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    estimated: bool,
    source: str,
    execution_id: str = "",
    module: str = "",
    operation: str = "",
    campaign_id: str = "",
    asset_type: str = "",
    metadata: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build a normalized success usage result."""

    return TokenUsage(
        provider=provider,
        model=model,
        input_tokens=max(0, int(input_tokens)),
        output_tokens=max(0, int(output_tokens)),
        total_tokens=max(0, int(total_tokens)),
        estimated=bool(estimated),
        source=source,
        execution_id=execution_id,
        module=module,
        operation=operation,
        campaign_id=campaign_id,
        asset_type=asset_type,
        metadata=metadata or {},
        warnings=warnings or [],
        errors=errors or [],
    ).to_dict()


def build_estimated_usage_result(
    *,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int = 0,
    source: str = "estimator",
    execution_id: str = "",
    module: str = "",
    operation: str = "",
    campaign_id: str = "",
    asset_type: str = "",
    metadata: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build an estimated usage result."""

    total_tokens = max(0, int(input_tokens)) + max(0, int(output_tokens))
    return build_success_usage_result(
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated=True,
        source=source,
        execution_id=execution_id,
        module=module,
        operation=operation,
        campaign_id=campaign_id,
        asset_type=asset_type,
        metadata=metadata,
        warnings=warnings,
        errors=errors,
    )


def build_unavailable_usage_result(
    *,
    provider: str = "",
    model: str = "",
    execution_id: str = "",
    module: str = "",
    operation: str = "",
    campaign_id: str = "",
    asset_type: str = "",
    metadata: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build a structured result for missing usage data."""

    return build_success_usage_result(
        provider=provider,
        model=model,
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated=False,
        source="unavailable",
        execution_id=execution_id,
        module=module,
        operation=operation,
        campaign_id=campaign_id,
        asset_type=asset_type,
        metadata=metadata,
        warnings=warnings or ["Token usage unavailable."],
        errors=errors or [],
    )


def build_failure_usage_result(
    *,
    provider: str = "",
    model: str = "",
    execution_id: str = "",
    module: str = "",
    operation: str = "",
    campaign_id: str = "",
    asset_type: str = "",
    metadata: dict[str, Any] | None = None,
    error: str = "Token tracking failed.",
) -> dict[str, Any]:
    """Build a structured failure usage result."""

    return build_success_usage_result(
        provider=provider,
        model=model,
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated=False,
        source="unavailable",
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
