"""Token tracking contracts and shared constants."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


TOKEN_FIELD_ALIASES = {
    "prompt_tokens": "input_tokens",
    "completion_tokens": "output_tokens",
    "input_tokens": "input_tokens",
    "output_tokens": "output_tokens",
    "total_tokens": "total_tokens",
}

TOKEN_SOURCE_VALUES = ("provider_usage", "estimator", "unavailable")


@dataclass(frozen=True)
class TokenUsageContract:
    """Serializable token usage contract."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated: bool
    source: str
    execution_id: str
    module: str
    operation: str
    campaign_id: str
    asset_type: str
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the contract."""

        return {
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated": self.estimated,
            "source": self.source,
            "execution_id": self.execution_id,
            "module": self.module,
            "operation": self.operation,
            "campaign_id": self.campaign_id,
            "asset_type": self.asset_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }
