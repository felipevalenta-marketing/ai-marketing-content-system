"""Reusable pytest fixtures for the AI Marketing Content System tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_brand_name() -> str:
    """Return the default sample brand."""

    return "wenzel_partner"


@pytest.fixture
def sample_generation_request(sample_brand_name: str) -> dict[str, object]:
    """Return a representative content generation request."""

    return {
        "brand": sample_brand_name,
        "platform": "instagram",
        "content_type": "property_description",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "extra_notes": "Rustic outside, modern comfort inside, close to Manacor and beaches.",
    }


@pytest.fixture
def sample_formatted_output() -> dict[str, object]:
    """Return a representative formatted property description."""

    return {
        "content_type": "property_description",
        "title": "Rustic home near Sant Llorenc des Cardassar",
        "short_description": "Calm Mallorca living with practical connectivity.",
        "long_description": "Rustic exterior, modern comfort inside, with access to Manacor and nearby beaches.",
        "highlights": ["Modern interiors", "Near services", "Mediterranean lifestyle"],
        "cta": "Request a viewing",
        "notes": "Sample formatted output for testing.",
        "raw_content": "Sample raw content.",
    }


@pytest.fixture
def sample_ai_response(sample_formatted_output: dict[str, object]) -> dict[str, object]:
    """Return a representative AI response payload."""

    return {
        "success": True,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "content": json.dumps(sample_formatted_output),
        "raw_response": {"content": json.dumps(sample_formatted_output)},
        "metadata": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "warnings": [],
        },
        "error": None,
    }


@pytest.fixture
def sample_parsed_output(sample_ai_response: dict[str, object]) -> dict[str, object]:
    """Return a representative parsed AI response."""

    return {
        "content": str(sample_ai_response["content"]),
        "hashtags": ["#mallorca", "#realestate"],
        "cta": "Request a viewing",
        "json": {
            "title": "Rustic home near Sant Llorenc des Cardassar",
            "short_description": "Calm Mallorca living with practical connectivity.",
            "long_description": "Rustic exterior, modern comfort inside, with access to Manacor and nearby beaches.",
            "highlights": ["Modern interiors", "Near services", "Mediterranean lifestyle"],
            "cta": "Request a viewing",
        },
        "raw_content": str(sample_ai_response["content"]),
        "parser_warnings": [],
    }


@pytest.fixture
def sample_prompt_payload(sample_generation_request: dict[str, object]) -> dict[str, object]:
    """Return a reusable prompt payload example."""

    return {
        "system_prompt": "System instructions for premium Mallorca real estate content.",
        "user_prompt": "Write a property description for a rustic home in Sant Llorenc des Cardassar.",
        "context_used": ["brand_config/tone.md", "knowledge_base/neighborhoods/sant_llorenc_des_cardassar.md"],
        "platform_rules": ["instagram"],
        "content_type": str(sample_generation_request["content_type"]),
        "brand": str(sample_generation_request["brand"]),
        "metadata": {
            "brand": str(sample_generation_request["brand"]),
            "platform": str(sample_generation_request["platform"]),
            "content_type": str(sample_generation_request["content_type"]),
            "objective": str(sample_generation_request["objective"]),
            "audience": str(sample_generation_request["audience"]),
        },
    }


@pytest.fixture
def sample_platform_variants() -> dict[str, object]:
    """Return representative platform variants."""

    return {
        "instagram": {
            "platform": "instagram",
            "content": {
                "hook": "Rustic calm in Mallorca",
                "caption": "Mediterranean living with practical connectivity.",
                "cta": "Request a viewing",
                "hashtags": ["#Mallorca"],
            },
            "content_variants": {"primary_variant": {"caption": "Mediterranean living with practical connectivity."}},
            "constraints": {},
            "contract": {},
            "warnings": [],
            "errors": [],
        }
    }


@pytest.fixture
def sample_governance_payload(sample_formatted_output: dict[str, object], sample_platform_variants: dict[str, object], sample_brand_name: str) -> dict[str, object]:
    """Return a representative governance payload."""

    return {
        "brand": sample_brand_name,
        "platform": "instagram",
        "content_type": "property_description",
        "formatted_output": sample_formatted_output,
        "platform_variants": sample_platform_variants,
        "metadata": {
            "audience": "relocation_clients",
            "location": "sant_llorenc_des_cardassar",
            "objective": "generate_leads",
        },
    }


@pytest.fixture
def sample_campaign_request(sample_brand_name: str) -> dict[str, object]:
    """Return a representative campaign request."""

    return {
        "brand": sample_brand_name,
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "platforms": ["instagram", "facebook", "linkedin", "email"],
        "assets_required": ["instagram_post", "instagram_reel", "image_prompt", "email_teaser", "linkedin_post"],
        "extra_notes": "Rustic exterior, modern comfort inside, close to Manacor and beaches.",
    }


@pytest.fixture
def sample_asset_request(sample_brand_name: str) -> dict[str, object]:
    """Return a representative asset coordination request."""

    return {
        "brand": sample_brand_name,
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "platforms": ["instagram", "facebook", "linkedin", "email"],
        "assets_required": ["text_caption", "image_prompt", "video_prompt", "email_teaser"],
        "creative_direction": "Rustic exterior, modern comfort inside, close to Manacor and beaches.",
        "visual_style": "Mediterranean, natural light, premium but approachable",
        "extra_notes": "Do not invent property facts.",
    }


@pytest.fixture
def sample_video_script_request(sample_brand_name: str) -> dict[str, object]:
    """Return a representative video script request."""

    return {
        "brand": sample_brand_name,
        "platform": "instagram",
        "content_type": "video_script",
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "video_type": "instagram_reel",
        "duration": "30s",
        "creative_direction": "Rustic exterior with modern comfort inside, close to Manacor and beaches.",
        "visual_style": "mediterranean_lifestyle",
        "tone": "premium but approachable",
        "extra_notes": "Do not invent property facts.",
    }


@pytest.fixture
def sample_video_script_ai_response() -> dict[str, object]:
    """Return a representative AI response for video script generation."""

    content = json.dumps(
        {
            "hook": "Discover a rustic Mallorca home with calm, modern comfort.",
            "script": "Start with the exterior, move into the bright living spaces, and finish with the lifestyle payoff.",
            "voiceover": "Discover a rustic Mallorca home with calm, modern comfort. Step inside, enjoy the light, and imagine the lifestyle.",
            "cta": "Contact our team to learn more.",
            "music_mood": "warm, modern, rhythmic, and elegant",
            "scene_sequence": [
                {
                    "scene_number": 1,
                    "duration": "6s",
                    "visual": "Strong exterior first impression with natural light.",
                    "camera_motion": "slow push-in",
                    "voiceover": "Discover a rustic Mallorca home with calm, modern comfort.",
                    "on_screen_text": "Rustic Mallorca calm",
                    "purpose": "Hook / first impression",
                },
                {
                    "scene_number": 2,
                    "duration": "6s",
                    "visual": "Exterior context with the surrounding lifestyle.",
                    "camera_motion": "gentle pan",
                    "voiceover": "Step inside, enjoy the light, and imagine the lifestyle.",
                    "on_screen_text": "Lifestyle context",
                    "purpose": "Exterior or lifestyle context",
                },
                {
                    "scene_number": 3,
                    "duration": "6s",
                    "visual": "Bright interior comfort and practical layout.",
                    "camera_motion": "steady glide",
                    "voiceover": "Bright interiors and a grounded Mediterranean feel.",
                    "on_screen_text": "Modern comfort",
                    "purpose": "Main property value",
                },
                {
                    "scene_number": 4,
                    "duration": "6s",
                    "visual": "Location relevance close to Manacor and beaches.",
                    "camera_motion": "slow reveal",
                    "voiceover": "Close to Manacor and the coast, with everyday convenience.",
                    "on_screen_text": "Well located",
                    "purpose": "Location or lifestyle relevance",
                },
                {
                    "scene_number": 5,
                    "duration": "6s",
                    "visual": "Final CTA frame with elegant brand close.",
                    "camera_motion": "settled frame",
                    "voiceover": "Contact our team to learn more.",
                    "on_screen_text": "Contact our team",
                    "purpose": "CTA",
                },
            ],
            "storyboard": [
                {
                    "frame_number": 1,
                    "scene_number": 1,
                    "shot_type": "wide",
                    "visual_description": "Strong exterior first impression with natural light.",
                    "camera_direction": "slow push-in",
                    "lighting": "natural daylight",
                    "motion": "slow push-in",
                    "on_screen_text": "Rustic Mallorca calm",
                    "voiceover": "Discover a rustic Mallorca home with calm, modern comfort.",
                }
            ],
            "camera_direction": {
                "platform": "instagram",
                "framing": "vertical-safe",
                "movement": ["slow push-in", "gentle pan", "steady glide", "slow reveal", "settled frame"],
                "shot_types": ["wide", "medium", "detail", "wide", "hero"],
                "continuity_note": "Maintain cinematic continuity and avoid fake luxury exaggeration.",
            },
        }
    )

    return {
        "success": True,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "content": content,
        "raw_response": {"content": content, "id": "dummy-video-script"},
        "metadata": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "warnings": [],
        },
        "error": None,
    }


@pytest.fixture
def sample_image_prompt_request(sample_brand_name: str) -> dict[str, object]:
    """Return a representative image prompt request."""

    return {
        "brand": sample_brand_name,
        "platform": "instagram",
        "content_type": "image_prompt",
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "visual_style": "mediterranean_lifestyle",
        "creative_direction": "Rustic exterior with modern comfort inside, close to Manacor and beaches.",
        "image_type": "property_exterior",
        "aspect_ratio": "4:5",
        "extra_notes": "Premium but approachable, realistic, no exaggerated luxury.",
    }


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Return a temporary output directory for export tests."""

    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def mock_openai_success_response():
    """Return a reusable mocked Responses API result."""

    class DummyResponse:
        def __init__(self, output_text: str) -> None:
            self.output_text = output_text

        def model_dump(self) -> dict[str, object]:
            return {"output_text": self.output_text, "id": "dummy-response"}

    return DummyResponse


@pytest.fixture
def mock_openai_failure_response() -> Exception:
    """Return a reusable mocked OpenAI failure."""

    return RuntimeError("mocked openai failure")
