from __future__ import annotations

from src.tracking.cost_calculator import CostCalculator


def test_cost_calculator_handles_cached_input_without_double_charge() -> None:
    calculator = CostCalculator()
    result = calculator.calculate_total_cost(
        input_tokens=1500,
        output_tokens=500,
        cached_input_tokens=500,
        input_per_1m=10.0,
        output_per_1m=20.0,
        cached_input_per_1m=1.0,
        round_decimals=6,
    )
    assert result["input_cost"] == 0.01
    assert result["output_cost"] == 0.01
    assert result["cached_input_cost"] == 0.0005
    assert result["total_cost"] == 0.0205


def test_cost_calculator_builds_cost_record(sample_token_usage: dict[str, object]) -> None:
    calculator = CostCalculator()
    pricing = {
        "currency": "USD",
        "input_per_1m": 5.0,
        "output_per_1m": 10.0,
        "cached_input_per_1m": 1.0,
    }
    result = calculator.calculate_cost_record(sample_token_usage, pricing, round_decimals=6)
    assert result["currency"] == "USD"
    assert "total_cost" in result
