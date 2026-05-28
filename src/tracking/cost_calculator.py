"""Cost calculation helpers."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from src.reporting.report_metrics import safe_float, safe_int, safe_text


class CostCalculator:
    """Calculate estimated usage costs from token counts and pricing data."""

    def calculate_input_cost(self, input_tokens: int, input_per_1m: float, *, cached_input_tokens: int = 0, cached_input_per_1m: float = 0.0) -> float:
        """Calculate input cost without double-charging cached tokens."""

        billable_input_tokens = max(0, safe_int(input_tokens, 0) - max(0, safe_int(cached_input_tokens, 0)))
        return self._rate_cost(billable_input_tokens, input_per_1m)

    def calculate_output_cost(self, output_tokens: int, output_per_1m: float) -> float:
        """Calculate output token cost."""

        return self._rate_cost(max(0, safe_int(output_tokens, 0)), output_per_1m)

    def calculate_cached_input_cost(self, cached_input_tokens: int, cached_input_per_1m: float) -> float:
        """Calculate cached input token cost."""

        return self._rate_cost(max(0, safe_int(cached_input_tokens, 0)), cached_input_per_1m)

    def calculate_total_cost(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        cached_input_tokens: int = 0,
        input_per_1m: float,
        output_per_1m: float,
        cached_input_per_1m: float = 0.0,
        round_decimals: int = 6,
    ) -> dict[str, float]:
        """Calculate cost components and total cost."""

        input_cost = self.calculate_input_cost(input_tokens, input_per_1m, cached_input_tokens=cached_input_tokens, cached_input_per_1m=cached_input_per_1m)
        output_cost = self.calculate_output_cost(output_tokens, output_per_1m)
        cached_input_cost = self.calculate_cached_input_cost(cached_input_tokens, cached_input_per_1m)
        total_cost = input_cost + output_cost + cached_input_cost
        return {
            "input_cost": self._round_cost(input_cost, round_decimals),
            "output_cost": self._round_cost(output_cost, round_decimals),
            "cached_input_cost": self._round_cost(cached_input_cost, round_decimals),
            "total_cost": self._round_cost(total_cost, round_decimals),
        }

    def calculate_cost_record(self, token_usage: dict[str, Any], pricing: dict[str, Any], round_decimals: int = 6) -> dict[str, Any]:
        """Calculate a cost record from token usage and a pricing lookup."""

        input_tokens = safe_int(token_usage.get("input_tokens"), 0)
        output_tokens = safe_int(token_usage.get("output_tokens"), 0)
        cached_input_tokens = safe_int(token_usage.get("cached_input_tokens"), 0)
        currency = safe_text(pricing.get("currency"), limit=32) or "USD"
        cost = self.calculate_total_cost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens,
            input_per_1m=safe_float(pricing.get("input_per_1m"), 0.0),
            output_per_1m=safe_float(pricing.get("output_per_1m"), 0.0),
            cached_input_per_1m=safe_float(pricing.get("cached_input_per_1m"), 0.0),
            round_decimals=round_decimals,
        )
        return {
            "currency": currency,
            **cost,
        }

    def _rate_cost(self, tokens: int, rate_per_1m: float) -> float:
        tokens_value = Decimal(str(max(0, tokens)))
        rate_value = Decimal(str(safe_float(rate_per_1m, 0.0)))
        return float((tokens_value / Decimal("1000000")) * rate_value)

    def _round_cost(self, value: float, round_decimals: int) -> float:
        quantize_target = Decimal("1").scaleb(-max(0, round_decimals))
        return float(Decimal(str(value)).quantize(quantize_target, rounding=ROUND_HALF_UP))
