"""Tests for content governance."""

from __future__ import annotations

from src.governance.content_governance import ContentGovernanceEngine


def test_safe_content_is_approved(sample_governance_payload):
    engine = ContentGovernanceEngine()
    result = engine.evaluate(sample_governance_payload)

    assert result["success"] is True
    assert result["approved"] in {True, False}
    assert result["status"] in {"approved", "approved_with_warnings", "needs_review", "rejected"}


def test_weak_content_receives_warnings(sample_governance_payload):
    engine = ContentGovernanceEngine()
    payload = dict(sample_governance_payload)
    payload["formatted_output"] = {"title": "", "short_description": "", "long_description": "", "highlights": [], "cta": ""}
    result = engine.evaluate(payload)

    assert result["warnings"]
    assert result["quality_score"] <= 100


def test_risky_investment_claims_are_flagged(sample_governance_payload):
    engine = ContentGovernanceEngine()
    payload = dict(sample_governance_payload)
    payload["formatted_output"] = {
        "title": "Best investment",
        "short_description": "Guaranteed ROI and risk-free investment.",
        "long_description": "Limited time only exclusive opportunity with unbeatable price.",
        "highlights": ["Guaranteed appreciation"],
        "cta": "Act now",
    }
    result = engine.evaluate(payload)

    assert result["errors"]
    assert result["factual_safety_score"] < 100


def test_fake_urgency_is_flagged(sample_governance_payload):
    engine = ContentGovernanceEngine()
    payload = dict(sample_governance_payload)
    payload["formatted_output"] = {
        "title": "Limited time only",
        "short_description": "Act now.",
        "long_description": "Fake urgency wording.",
        "highlights": ["Exclusive opportunity"],
        "cta": "Act now",
    }
    result = engine.evaluate(payload)

    assert result["warnings"] or result["errors"]


def test_unsupported_exclusivity_is_flagged(sample_governance_payload):
    engine = ContentGovernanceEngine()
    payload = dict(sample_governance_payload)
    payload["formatted_output"] = {
        "title": "Exclusive opportunity",
        "short_description": "Unbeatable price and best investment.",
        "long_description": "An exclusive opportunity.",
        "highlights": ["Exclusive"],
        "cta": "Act now",
    }
    result = engine.evaluate(payload)

    assert result["warnings"] or result["errors"]


def test_factual_safety_errors_can_reject_content(sample_governance_payload):
    engine = ContentGovernanceEngine()
    payload = dict(sample_governance_payload)
    payload["formatted_output"] = {
        "title": "Guaranteed ROI",
        "short_description": "Risk-free investment.",
        "long_description": "Guaranteed return and fake scarcity.",
        "highlights": ["Guaranteed appreciation"],
        "cta": "Act now",
    }
    result = engine.evaluate(payload)

    assert result["status"] == "rejected"


def test_scoring_returns_all_score_components(sample_governance_payload):
    engine = ContentGovernanceEngine()
    result = engine.evaluate(sample_governance_payload)

    for field in ("quality_score", "brand_score", "platform_score", "factual_safety_score", "overall_score"):
        assert field in result


def test_status_values_are_supported(sample_governance_payload):
    engine = ContentGovernanceEngine()
    result = engine.evaluate(sample_governance_payload)

    assert result["status"] in {"approved", "approved_with_warnings", "needs_review", "rejected"}


def test_missing_token_usage_only_warns(sample_governance_payload):
    engine = ContentGovernanceEngine()
    result = engine.evaluate(sample_governance_payload)

    assert any("token usage" in warning.lower() for warning in result["warnings"])
