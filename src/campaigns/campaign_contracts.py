"""Reusable contracts for deterministic campaign composition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.utils.file_utils import normalize_key


SUPPORTED_CAMPAIGN_TYPES = (
    "property_launch",
    "relocation_campaign",
    "neighborhood_spotlight",
    "reform_opportunity",
    "lifestyle_campaign",
    "investment_angle",
    "brand_awareness",
    "lead_generation",
    "email_sequence",
    "paid_ads_campaign",
    "seo_campaign",
    "video_campaign",
    "open_house_campaign",
    "seller_acquisition_campaign",
)


@dataclass(frozen=True)
class CampaignContract:
    """Describe the structural expectations for a campaign type."""

    campaign_type: str
    required_fields: tuple[str, ...]
    required_assets: tuple[str, ...]
    platform_plan: dict[str, list[str]]
    content_sequence: list[dict[str, str]]
    cta_strategy: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the campaign contract."""

        return {
            "campaign_type": self.campaign_type,
            "required_fields": list(self.required_fields),
            "required_assets": list(self.required_assets),
            "platform_plan": self.platform_plan,
            "content_sequence": self.content_sequence,
            "cta_strategy": self.cta_strategy,
            "notes": self.notes,
        }


CAMPAIGN_CONTRACTS: dict[str, CampaignContract] = {
    "property_launch": CampaignContract(
        campaign_type="property_launch",
        required_fields=("campaign_name", "main_message", "target_audience", "property_angle", "platform_plan", "required_assets", "cta_strategy"),
        required_assets=("instagram_post", "instagram_reel", "property_description", "image_prompt", "email_teaser", "linkedin_post"),
        platform_plan={
            "instagram": ["instagram_post", "instagram_reel", "image_prompt"],
            "facebook": ["facebook_post"],
            "linkedin": ["linkedin_post"],
            "email": ["email_teaser"],
            "website_listing": ["property_description"],
        },
        content_sequence=[
            {"step": "awareness_post", "asset_type": "instagram_post"},
            {"step": "reel_hook", "asset_type": "instagram_reel"},
            {"step": "property_description", "asset_type": "property_description"},
            {"step": "email_teaser", "asset_type": "email_teaser"},
            {"step": "conversion_cta", "asset_type": "campaign_cta_set"},
        ],
        cta_strategy="elegant direct conversion",
        notes=["Property-led launch narrative with multi-platform sequencing."],
    ),
    "relocation_campaign": CampaignContract(
        campaign_type="relocation_campaign",
        required_fields=("campaign_name", "relocation_angle", "buyer_concern", "lifestyle_message", "trust_message", "platform_plan", "required_assets"),
        required_assets=("instagram_post", "linkedin_post", "email_teaser", "website_listing"),
        platform_plan={
            "instagram": ["instagram_post", "instagram_reel"],
            "facebook": ["facebook_post"],
            "linkedin": ["linkedin_post"],
            "email": ["email_teaser"],
            "website_listing": ["website_listing"],
        },
        content_sequence=[
            {"step": "lifestyle_problem", "asset_type": "instagram_post"},
            {"step": "neighborhood_solution", "asset_type": "linkedin_post"},
            {"step": "property_fit", "asset_type": "website_listing"},
            {"step": "trust_message", "asset_type": "email_teaser"},
            {"step": "lead_cta", "asset_type": "campaign_cta_set"},
        ],
        cta_strategy="trust-building lead capture",
        notes=["Reassuring relocation narrative with practical support and local expertise."],
    ),
    "neighborhood_spotlight": CampaignContract(
        campaign_type="neighborhood_spotlight",
        required_fields=("campaign_name", "area_positioning", "lifestyle_hooks", "local_relevance", "platform_plan", "required_assets"),
        required_assets=("instagram_post", "instagram_reel", "linkedin_post", "website_listing"),
        platform_plan={
            "instagram": ["instagram_post", "instagram_reel"],
            "linkedin": ["linkedin_post"],
            "email": ["email_teaser"],
            "website_listing": ["website_listing"],
        },
        content_sequence=[
            {"step": "area_introduction", "asset_type": "instagram_post"},
            {"step": "lifestyle_angle", "asset_type": "instagram_reel"},
            {"step": "property_opportunity", "asset_type": "website_listing"},
            {"step": "local_credibility", "asset_type": "linkedin_post"},
            {"step": "cta", "asset_type": "campaign_cta_set"},
        ],
        cta_strategy="area discovery",
        notes=["Place-led storytelling anchored in local relevance."],
    ),
    "reform_opportunity": CampaignContract(
        campaign_type="reform_opportunity",
        required_fields=("campaign_name", "renovation_potential", "value_add_angle", "factual_safety_notes", "visual_direction", "platform_plan", "required_assets"),
        required_assets=("instagram_post", "image_prompt", "property_description", "linkedin_post"),
        platform_plan={
            "instagram": ["instagram_post", "instagram_reel", "image_prompt"],
            "linkedin": ["linkedin_post"],
            "website_listing": ["property_description"],
        },
        content_sequence=[
            {"step": "reform_potential", "asset_type": "instagram_post"},
            {"step": "visual_direction", "asset_type": "image_prompt"},
            {"step": "value_add", "asset_type": "website_listing"},
            {"step": "safety_note", "asset_type": "campaign_summary"},
        ],
        cta_strategy="opportunity with caution",
        notes=["Value-add framing with explicit factual safety guardrails."],
    ),
    "lifestyle_campaign": CampaignContract(
        campaign_type="lifestyle_campaign",
        required_fields=("campaign_name", "emotional_driver", "visual_direction", "storytelling_arc", "platform_plan", "required_assets"),
        required_assets=("instagram_post", "instagram_reel", "image_prompt", "video_prompt"),
        platform_plan={"instagram": ["instagram_post", "instagram_reel"], "video": ["video_prompt"]},
        content_sequence=[
            {"step": "emotion", "asset_type": "instagram_post"},
            {"step": "visual", "asset_type": "image_prompt"},
            {"step": "motion", "asset_type": "video_prompt"},
        ],
        cta_strategy="lifestyle discovery",
        notes=["Emotion-led positioning with visual-first sequencing."],
    ),
    "investment_angle": CampaignContract(
        campaign_type="investment_angle",
        required_fields=("campaign_name", "opportunity_framing", "factual_safety_guardrails", "risk_aware_messaging", "platform_plan", "required_assets"),
        required_assets=("linkedin_post", "website_listing", "email_teaser"),
        platform_plan={"linkedin": ["linkedin_post"], "email": ["email_teaser"], "website_listing": ["website_listing"]},
        content_sequence=[
            {"step": "opportunity", "asset_type": "linkedin_post"},
            {"step": "risk_guardrails", "asset_type": "campaign_summary"},
            {"step": "conversion", "asset_type": "email_teaser"},
        ],
        cta_strategy="risk-aware conversion",
        notes=["No guaranteed ROI claims; must remain factual and measured."],
    ),
    "brand_awareness": CampaignContract(
        campaign_type="brand_awareness",
        required_fields=("campaign_name", "brand_message", "trust_positioning", "audience_education", "service_positioning", "platform_sequence", "required_assets"),
        required_assets=("instagram_post", "linkedin_post", "facebook_post"),
        platform_plan={"instagram": ["instagram_post"], "facebook": ["facebook_post"], "linkedin": ["linkedin_post"]},
        content_sequence=[
            {"step": "brand_message", "asset_type": "instagram_post"},
            {"step": "trust", "asset_type": "linkedin_post"},
            {"step": "community", "asset_type": "facebook_post"},
        ],
        cta_strategy="trust-first discovery",
        notes=["Brand trust and service education across awareness channels."],
    ),
}


def normalize_campaign_type(campaign_type: str) -> str:
    """Normalize campaign type names."""

    return normalize_key(campaign_type)


def get_campaign_contract(campaign_type: str) -> CampaignContract:
    """Return the contract for a campaign type."""

    key = normalize_campaign_type(campaign_type)
    return CAMPAIGN_CONTRACTS.get(key, CAMPAIGN_CONTRACTS["property_launch"])


def list_supported_campaign_types() -> list[str]:
    """Return canonical campaign types."""

    return sorted(CAMPAIGN_CONTRACTS.keys())
