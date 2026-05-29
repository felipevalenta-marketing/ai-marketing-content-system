from __future__ import annotations

from src.analytics.insight_generator import InsightGenerator


def test_insight_generator_flags_missing_data() -> None:
    generator = InsightGenerator()
    analytics = {"sections": {"storage": {"records_count": 0}, "workflows": {"failed_workflows": 1}, "costs": {"unknown_pricing_records": 1}, "governance": {"warning_count": 1}}}

    insights = generator.generate_insights(analytics)
    recommendations = generator.generate_recommendations(analytics)

    assert any("No persisted records" in item for item in insights)
    assert any("pricing" in item.lower() for item in recommendations)
    assert any("workflow" in item.lower() for item in recommendations)

