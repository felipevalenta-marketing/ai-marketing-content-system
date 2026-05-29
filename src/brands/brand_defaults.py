"""Safe default settings for brand-aware generation."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


GENERIC_BRAND_DEFAULTS: dict[str, Any] = {
    "default_platform": "instagram",
    "default_content_type": "instagram_post",
    "default_campaign_type": "property_launch",
    "default_objective": "generate_leads",
    "default_audience": "relocation_clients",
    "default_visual_style": "mediterranean_lifestyle",
    "default_language": "en",
}

BRAND_DEFAULTS: dict[str, dict[str, Any]] = {
    "wenzel_partner": {
        "display_name": "Wenzel & Partner",
        "default_platform": "instagram",
        "default_content_type": "instagram_post",
        "default_campaign_type": "property_launch",
        "default_objective": "generate_leads",
        "default_audience": "relocation_clients",
        "default_visual_style": "mediterranean_lifestyle",
        "default_language": "en",
    },
}


def normalize_brand_defaults(defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = deepcopy(GENERIC_BRAND_DEFAULTS)
    if isinstance(defaults, dict):
        merged.update({key: value for key, value in defaults.items() if value not in (None, "")})
    return merged


def get_brand_defaults(brand_id: str) -> dict[str, Any]:
    brand_key = str(brand_id or "").strip().lower()
    return normalize_brand_defaults(BRAND_DEFAULTS.get(brand_key))


def merge_brand_defaults(base_defaults: dict[str, Any] | None = None, brand_defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    merged = normalize_brand_defaults(base_defaults)
    if isinstance(brand_defaults, dict):
        merged.update({key: value for key, value in brand_defaults.items() if value not in (None, "")})
    return normalize_brand_defaults(merged)


def list_brand_defaults() -> dict[str, dict[str, Any]]:
    return {brand_id: normalize_brand_defaults(defaults) for brand_id, defaults in BRAND_DEFAULTS.items()}
