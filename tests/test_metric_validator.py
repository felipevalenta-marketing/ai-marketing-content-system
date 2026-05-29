from __future__ import annotations

from src.analytics.metric_validator import MetricValidator


def test_metric_validator_accepts_valid_payload() -> None:
    validator = MetricValidator()
    result = validator.validate({"analytics_type": "executive_dashboard", "date_range": {"start": "", "end": ""}, "filters": {}, "kpis": {}, "sections": {}, "trends": {}})

    assert result["valid"] is True


def test_metric_validator_detects_secrets() -> None:
    validator = MetricValidator()
    result = validator.validate({"analytics_type": "executive_dashboard", "kpis": {}, "sections": {}, "trends": {}, "notes": "OPENAI_API_KEY=sk-test"})

    assert result["valid"] is False
    assert result["errors"]

