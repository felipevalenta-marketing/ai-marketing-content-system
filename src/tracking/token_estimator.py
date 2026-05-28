"""Token estimation utilities."""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - optional dependency
    import tiktoken
except Exception:  # pragma: no cover - optional dependency fallback
    tiktoken = None

from src.reporting.report_metrics import safe_text
from src.tracking.token_result import build_estimated_usage_result, build_unavailable_usage_result


class TokenEstimator:
    """Estimate token usage when provider usage metadata is unavailable."""

    def estimate_text_tokens(self, text: str, model: str | None = None) -> int:
        """Estimate input tokens for a text payload."""

        normalized = safe_text(text, limit=200000)
        if not normalized:
            return 0

        if tiktoken is not None:
            try:
                encoding = tiktoken.encoding_for_model(model or "")
            except Exception:  # pragma: no cover - model fallback
                encoding = None
            if encoding is not None:
                try:
                    return max(1, len(encoding.encode(normalized)))
                except Exception:  # pragma: no cover - fallback
                    pass
        return max(1, round(len(normalized) / 4))

    def estimate_output_tokens(self, text: str, model: str | None = None) -> int:
        """Estimate output tokens for generated text."""

        return self.estimate_text_tokens(text, model=model)

    def estimate_usage(
        self,
        *,
        input_text: str,
        output_text: str | None = None,
        provider: str = "",
        model: str = "",
        metadata: dict[str, Any] | None = None,
        execution_id: str = "",
        module: str = "",
        operation: str = "",
        campaign_id: str = "",
        asset_type: str = "",
    ) -> dict[str, Any]:
        """Return an estimated usage record."""

        input_tokens = self.estimate_text_tokens(input_text, model=model)
        output_tokens = self.estimate_output_tokens(output_text or "", model=model) if output_text is not None else 0
        if input_tokens <= 0 and output_tokens <= 0:
            return build_unavailable_usage_result(
                provider=provider,
                model=model,
                execution_id=execution_id,
                module=module,
                operation=operation,
                campaign_id=campaign_id,
                asset_type=asset_type,
                metadata=metadata or {},
                warnings=["Token usage unavailable and no text was provided for estimation."],
            )
        return build_estimated_usage_result(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            source="estimator",
            execution_id=execution_id,
            module=module,
            operation=operation,
            campaign_id=campaign_id,
            asset_type=asset_type,
            metadata=metadata or {},
            warnings=["Token usage estimated from text length."],
        )

    def estimate_future_usage(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Placeholder for future provider-side token accounting endpoints."""

        return self.estimate_usage(*args, **kwargs)
