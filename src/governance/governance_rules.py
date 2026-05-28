"""Reusable governance rules for deterministic content evaluation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


GOVERNANCE_RULES: dict[str, Any] = {
    "banned_phrases": [
        "risk-free investment",
        "guaranteed return",
        "guaranteed ROI",
        "guaranteed appreciation",
        "best investment",
        "limited time only",
        "exclusive opportunity",
        "unbeatable price",
        "fake exclusivity",
        "fake scarcity",
        "fake urgency",
    ],
    "risky_claims": [
        "guaranteed return",
        "guaranteed investment",
        "guaranteed appreciation",
        "risk-free investment",
        "best investment",
        "unbeatable price",
        "limited time only",
    ],
    "generic_ai_phrases": [
        "in today’s fast-paced world",
        "elevate your lifestyle",
        "discover the perfect blend",
        "luxury living at its finest",
        "step into a world",
        "a perfect opportunity",
    ],
    "excessive_hype_terms": [
        "ultimate",
        "exclusive",
        "unparalleled",
        "world-class",
        "iconic",
        "revolutionary",
        "best",
    ],
    "platform_rules": {
        "instagram": {
            "min_hashtags": 1,
            "max_hashtags": 10,
            "requires_hook": True,
            "requires_cta": True,
            "forbidden_styles": ["overly formal"],
        },
        "facebook": {
            "min_hashtags": 0,
            "max_hashtags": 5,
            "requires_cta": True,
            "forbidden_styles": ["too terse"],
        },
        "linkedin": {
            "min_hashtags": 0,
            "max_hashtags": 3,
            "requires_cta": True,
            "forbidden_styles": ["overly emotional"],
        },
        "email": {
            "requires_subject": True,
            "requires_preview_text": True,
            "requires_cta": True,
            "forbidden_styles": ["hashtags"],
        },
        "website_listing": {
            "requires_title": True,
            "requires_description": True,
            "requires_highlights": True,
            "forbidden_styles": ["hashtags", "hype"],
        },
    },
    "score_thresholds": {
        "approved": 85.0,
        "approved_with_warnings": 70.0,
        "needs_review": 55.0,
    },
    "brand_tone_signals": {
        "positive": [
            "trustworthy",
            "local",
            "professional",
            "human",
            "premium",
            "approachable",
            "lifestyle-aware",
            "market-aware",
        ],
        "negative": [
            "ultra-luxury-only",
            "hard sell",
            "aggressive",
            "spammy",
            "overhyped",
            "generic",
        ],
    },
    "real_estate_safety_rules": {
        "critical_phrases": [
            "guaranteed roi",
            "guaranteed return",
            "risk-free investment",
            "fake exclusivity",
            "fake scarcity",
            "fake urgency",
        ],
        "warning_phrases": [
            "best investment",
            "unbeatable price",
            "exclusive opportunity",
            "limited time only",
        ],
        "unsupported_claim_phrases": [
            "invented distance",
            "invented location",
            "invented feature",
            "unverified amenity",
            "unverified price",
            "unverified legal claim",
        ],
    },
}


def get_governance_rules() -> dict[str, Any]:
    """Return a deep copy of the governance rules."""

    return deepcopy(GOVERNANCE_RULES)
