"""Platform and media requirements for asset coordination."""

from __future__ import annotations

from typing import Any

from src.assets.asset_contracts import normalize_asset_type
from src.utils.file_utils import normalize_key


PLATFORM_ALIASES: dict[str, str] = {
    "website_listing": "website",
    "web": "website",
    "seo_page": "website",
    "seo": "website",
}


PLATFORM_REQUIREMENTS: dict[str, dict[str, Any]] = {
    "instagram": {
        "asset_types": ["social_post", "reel_script", "image_prompt"],
        "creative_notes": [
            "Prefer vertical or square creative.",
            "Keep captions visual and concise.",
            "Use elegant direct CTAs and limited hashtags.",
        ],
    },
    "facebook": {
        "asset_types": ["social_post", "image_prompt"],
        "creative_notes": [
            "Use warmer community framing.",
            "Allow slightly more explanation.",
            "Keep hashtags modest and CTA softer.",
        ],
    },
    "linkedin": {
        "asset_types": ["social_post", "campaign_summary", "website_listing"],
        "creative_notes": [
            "Use professional and strategic framing.",
            "Minimize hashtags.",
            "Emphasize trust and market insight.",
        ],
    },
    "email": {
        "asset_types": ["email_teaser", "campaign_summary"],
        "creative_notes": [
            "Use subject, preview text, body, and CTA.",
            "Do not use hashtags.",
        ],
    },
    "website": {
        "asset_types": ["website_listing", "campaign_summary"],
        "creative_notes": [
            "Prioritize factual detail and readability.",
            "Keep SEO-ready structure.",
            "Avoid hashtags and unsupported claims.",
        ],
    },
}


IMAGE_REQUIREMENTS = {
    "asset_types": ["image_prompt"],
    "required_fields": ["subject", "composition", "lighting", "style", "aspect_ratio", "negative_prompt", "platform_use"],
    "visual_style_field": "visual_style",
    "readiness_fields": ["image_type", "visual_style", "aspect_ratio", "creative_direction"],
    "creative_notes": [
        "Specify aspect ratio, subject, lighting, composition, and negative prompt.",
        "Keep brand visual consistency and realism.",
    ],
}


VIDEO_REQUIREMENTS = {
    "asset_types": ["video_prompt"],
    "required_fields": ["scene_description", "camera_motion", "sequence", "mood", "duration", "voiceover_direction", "platform_use"],
    "creative_notes": [
        "Specify sequence, duration, camera motion, and voiceover direction.",
        "Keep cinematic direction grounded and practical.",
    ],
}


def get_platform_requirements(platform: str) -> dict[str, Any]:
    """Return the creative requirements for a platform."""

    key = normalize_key(platform)
    key = PLATFORM_ALIASES.get(key, key)
    return dict(PLATFORM_REQUIREMENTS.get(key, {"asset_types": [], "creative_notes": [f"No explicit requirements registered for {key}."]}))


def get_asset_type_requirements(asset_type: str) -> dict[str, Any]:
    """Return requirements for a specific asset type."""

    key = normalize_asset_type(asset_type)
    if key == "image_prompt":
        return dict(IMAGE_REQUIREMENTS)
    if key == "video_prompt":
        return dict(VIDEO_REQUIREMENTS)
    contract = get_asset_requirement_template(key)
    return dict(contract)


def build_asset_requirements(request: dict[str, Any]) -> dict[str, Any]:
    """Compile asset requirements from a request."""

    platforms = [normalize_key(platform) for platform in request.get("platforms", []) if str(platform).strip()]
    assets_required = [normalize_asset_type(asset) for asset in request.get("assets_required", []) if str(asset).strip()]
    platform_requirements = {platform: get_platform_requirements(platform) for platform in platforms}
    asset_requirements = {asset_type: get_asset_type_requirements(asset_type) for asset_type in assets_required}
    return {
        "platform_requirements": platform_requirements,
        "asset_requirements": asset_requirements,
        "image_requirements": dict(IMAGE_REQUIREMENTS),
        "video_requirements": dict(VIDEO_REQUIREMENTS),
        "image_prompt_readiness": {
            "image_type": normalize_key(str(request.get("image_type", ""))),
            "visual_style": str(request.get("visual_style", "")).strip(),
            "aspect_ratio": str(request.get("aspect_ratio", "")).strip(),
            "creative_direction": str(request.get("creative_direction", "")).strip(),
            "ready": all(
                [
                    str(request.get("image_type", "")).strip(),
                    str(request.get("visual_style", "")).strip(),
                    str(request.get("aspect_ratio", "")).strip(),
                    str(request.get("creative_direction", "")).strip(),
                ]
            ),
        },
        "campaign_alignment": {
            "campaign_type": normalize_key(str(request.get("campaign_type", ""))),
            "objective": str(request.get("objective", "")).strip(),
            "audience": str(request.get("audience", "")).strip(),
            "location": normalize_key(str(request.get("location", ""))),
            "property_type": normalize_key(str(request.get("property_type", ""))),
        },
        "creative_direction": str(request.get("creative_direction", "")).strip(),
        "visual_style": str(request.get("visual_style", "")).strip(),
        "extra_notes": str(request.get("extra_notes", "")).strip(),
    }


def get_asset_requirement_template(asset_type: str) -> dict[str, Any]:
    """Return a lightweight requirement template for non-media assets."""

    key = normalize_asset_type(asset_type)
    templates: dict[str, dict[str, Any]] = {
        "text_caption": {"required_fields": ["platform", "hook", "caption", "cta", "hashtags", "governance_status"], "creative_notes": ["Ready for social packaging."]},
        "social_post": {"required_fields": ["platform", "hook", "caption", "cta", "hashtags"], "creative_notes": ["Ready for social packaging."]},
        "reel_script": {"required_fields": ["hook", "script", "scenes", "voiceover_direction", "cta", "visual_direction"], "creative_notes": ["Ready for reel production planning."]},
        "property_description": {"required_fields": ["title", "short_description", "long_description", "highlights", "cta"], "creative_notes": ["Ready for website and listing workflows."]},
        "email_teaser": {"required_fields": ["subject", "preview_text", "body", "cta"], "creative_notes": ["Ready for email nurture workflows."]},
        "website_listing": {"required_fields": ["title", "short_description", "long_description", "highlights", "cta"], "creative_notes": ["Ready for website publishing."]},
        "campaign_summary": {"required_fields": ["campaign_name", "objective", "main_message", "assets"], "creative_notes": ["Campaign overview and governance summary."]},
        "campaign_bundle": {"required_fields": ["campaign_name", "assets", "platform_plan", "governance_summary"], "creative_notes": ["Bundle of coordinated assets."]},
    }
    return templates.get(key, {"required_fields": ["raw_content"], "creative_notes": ["Future-ready placeholder requirements."]})
