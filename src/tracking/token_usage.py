"""Token usage models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.reporting.report_metrics import utc_now_iso


@dataclass(frozen=True)
class TokenUsage:
    """Normalized token usage record."""

    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated: bool
    source: str
    timestamp: str = field(default_factory=utc_now_iso)
    operation: str = ""
    module: str = ""
    campaign_id: str = ""
    asset_type: str = ""
    execution_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the usage record."""

        return {
            "provider": self.provider,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "estimated": self.estimated,
            "source": self.source,
            "timestamp": self.timestamp,
            "operation": self.operation,
            "module": self.module,
            "campaign_id": self.campaign_id,
            "asset_type": self.asset_type,
            "execution_id": self.execution_id,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }
