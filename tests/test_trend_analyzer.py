from __future__ import annotations

from src.analytics.trend_analyzer import TrendAnalyzer


def test_trend_analyzer_groups_activity() -> None:
    analyzer = TrendAnalyzer()
    records = [
        {"record_id": "1", "record_type": "workflow", "brand": "wenzel_partner", "platform": "instagram", "created_at": "2026-05-29T09:00:00+00:00"},
        {"record_id": "2", "record_type": "report", "brand": "wenzel_partner", "platform": "facebook", "created_at": "2026-05-29T10:00:00+00:00"},
        {"record_id": "3", "record_type": "asset", "brand": "another_brand", "platform": "instagram", "created_at": "2026-05-28T11:00:00+00:00"},
    ]

    by_day = analyzer.group_by_day(records)
    by_brand = analyzer.group_by_brand(records)
    by_platform = analyzer.group_by_platform(records)
    recent = analyzer.summarize_recent_activity(records, limit=2)

    assert by_day["groups"]["2026-05-29"] == 2
    assert by_brand["groups"]["wenzel_partner"] == 2
    assert by_platform["groups"]["instagram"] == 2
    assert recent[0]["record_id"] == "2"
    assert recent[1]["record_id"] == "1"

