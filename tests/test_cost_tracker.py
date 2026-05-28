from __future__ import annotations

from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.tracking.cost_tracker import CostTracker


def test_cost_tracker_handles_unknown_pricing(sample_token_usage: dict[str, object]) -> None:
    tracker = CostTracker()
    result = tracker.track_cost(sample_token_usage, metadata={"provider": "openai", "model": "gpt-4o-mini"})
    assert result["success"] is True
    assert result["pricing_found"] is False
    assert result["estimated_cost"] is True
    assert result["warnings"]


def test_cost_tracker_supports_pricing_override(sample_token_usage: dict[str, object], monkeypatch) -> None:
    tracker = CostTracker()
    monkeypatch.setattr(
        tracker.mapper,
        "lookup_pricing",
        lambda provider, model: {
            "provider": provider,
            "model": model,
            "currency": "USD",
            "input_per_1m": 10.0,
            "output_per_1m": 20.0,
            "cached_input_per_1m": 1.0,
            "pricing_source": "configurable",
            "pricing_version": "test",
            "effective_date": "2026-01-01",
            "notes": "",
            "pricing_found": True,
        },
    )
    result = tracker.track_cost(sample_token_usage, metadata={"provider": "openai", "model": "gpt-4o-mini"})
    assert result["pricing_found"] is True
    assert result["total_cost"] > 0


def test_cost_tracker_aggregates_by_campaign(sample_cost_usage: dict[str, object]) -> None:
    tracker = CostTracker()
    summary = tracker.aggregate_campaign_cost([sample_cost_usage], campaign_id="campaign-1")
    assert summary["campaign_id"] == "campaign-1"
    assert "campaign-1" in summary["summary"]


def test_pipeline_includes_cost_tracking(sample_generation_request: dict[str, object], sample_token_usage: dict[str, object], monkeypatch) -> None:
    pipeline = ContentGenerationPipeline()
    monkeypatch.setattr(pipeline, "_can_generate_live", lambda: True)
    monkeypatch.setattr(
        pipeline,
        "generate_ai_response",
        lambda prompt_payload: {
            "success": True,
            "provider": "openai",
            "model": "gpt-4o-mini",
            "content": "Sample generation response.",
            "token_usage": sample_token_usage,
            "metadata": {},
            "error": None,
        },
    )
    result = pipeline.generate(dict(sample_generation_request))
    assert result["success"] is True
    assert result["token_usage"]["provider"] == "openai"
    assert result["cost_usage"]["provider"] == "openai"
    assert result["execution_cost_summary"] is not None
    assert result["provider_cost_summary"] is not None
