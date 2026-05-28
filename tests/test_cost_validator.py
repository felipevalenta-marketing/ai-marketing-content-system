from __future__ import annotations

from src.tracking.cost_validator import CostValidator


def test_cost_validator_accepts_valid_payload(sample_cost_usage: dict[str, object]) -> None:
    validator = CostValidator()
    result = validator.validate(sample_cost_usage)
    assert result["valid"] is True


def test_cost_validator_rejects_malformed_payload() -> None:
    validator = CostValidator()
    result = validator.validate({"provider": "", "input_tokens": -1, "total_cost": -1.0})
    assert result["valid"] is False
    assert result["errors"]
