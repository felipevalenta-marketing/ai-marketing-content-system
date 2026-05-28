"""Cost tracking contracts and constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.reporting.report_metrics import utc_now_iso


DEFAULT_COST_CURRENCY = "USD"
MAX_COST_DECIMALS = 6

COST_FIELD_ALIASES = {
    "prompt_tokens": "input_tokens",
    "completion_tokens": "output_tokens",
    "cached_prompt_tokens": "cached_input_tokens",
    "cached_tokens": "cached_input_tokens",
    "price_version": "pricing_version",
    "pricingVersion": "pricing_version",
}

COST_SOURCE_VALUES = ("provider_pricing", "registry", "unknown")


@dataclass(frozen=True)
class CostPricingContract:
    """Normalized pricing table record."""

    provider: str
    model: str
    currency: str = DEFAULT_COST_CURRENCY
    input_per_1m: float = 0.0
    output_per_1m: float = 0.0
    cached_input_per_1m: float = 0.0
    pricing_source: str = "configurable"
    pricing_version: str = "local_default"
    effective_date: str = ""
    notes: str = ""
    pricing_found: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the pricing contract."""

        return {
            "provider": self.provider,
            "model": self.model,
            "currency": self.currency,
            "input_per_1m": self.input_per_1m,
            "output_per_1m": self.output_per_1m,
            "cached_input_per_1m": self.cached_input_per_1m,
            "pricing_source": self.pricing_source,
            "pricing_version": self.pricing_version,
            "effective_date": self.effective_date,
            "notes": self.notes,
            "pricing_found": self.pricing_found,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CostUsageContract:
    """Normalized cost usage record."""

    provider: str
    model: str
    currency: str
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    cached_input_cost: float
    total_cost: float
    estimated_tokens: bool
    estimated_cost: bool
    pricing_found: bool
    pricing_version: str
    pricing_source: str
    execution_id: str = ""
    module: str = ""
    operation: str = ""
    campaign_id: str = ""
    asset_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the usage contract."""

        return {
            "success": True,
            "provider": self.provider,
            "model": self.model,
            "currency": self.currency,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_input_tokens": self.cached_input_tokens,
            "total_tokens": self.total_tokens,
            "input_cost": self.input_cost,
            "output_cost": self.output_cost,
            "cached_input_cost": self.cached_input_cost,
            "total_cost": self.total_cost,
            "estimated_tokens": self.estimated_tokens,
            "estimated_cost": self.estimated_cost,
            "pricing_found": self.pricing_found,
            "pricing_version": self.pricing_version,
            "pricing_source": self.pricing_source,
            "execution_id": self.execution_id,
            "module": self.module,
            "operation": self.operation,
            "campaign_id": self.campaign_id,
            "asset_type": self.asset_type,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class CostAggregationContract:
    """Structured aggregation payload for cost summaries."""

    summary: dict[str, Any]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": True,
            "summary": self.summary,
            "warnings": self.warnings,
            "errors": self.errors,
        }
