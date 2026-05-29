from __future__ import annotations

from src.analytics.metric_aggregator import MetricAggregator


def test_metric_aggregator_groups_brand_id_fallback() -> None:
    aggregator = MetricAggregator()

    result = aggregator.aggregate_by_brand(
        [
            {"brand_id": "wenzel_partner"},
            {"brand_id": "wenzel_partner"},
            {"brand_id": "other_brand"},
        ]
    )

    assert result["groups"]["wenzel_partner"] == 2
    assert result["groups"]["other_brand"] == 1
