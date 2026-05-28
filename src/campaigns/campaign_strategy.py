"""Campaign strategy construction for multi-platform packs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime, timezone

from src.campaigns.campaign_contracts import get_campaign_contract, normalize_campaign_type
from src.utils.file_utils import normalize_key


PLATFORM_ROLE_MAP: dict[str, str] = {
    "instagram": "visual awareness and lifestyle discovery",
    "facebook": "community warmth and explanation",
    "linkedin": "authority, market insight, and trust",
    "email": "direct nurturing and conversion",
    "website_listing": "detailed factual information",
}


@dataclass(frozen=True)
class CampaignStrategy:
    """Strategic campaign blueprint."""

    campaign_type: str
    campaign_name: str
    objective: str
    target_audience: str
    core_message: str
    emotional_angle: str
    rational_angle: str
    cta_strategy: str
    platform_role: dict[str, str]
    asset_role: dict[str, str]
    content_sequence: list[dict[str, str]]
    visual_direction: str
    governance_sensitivity_level: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "campaign_type": self.campaign_type,
            "campaign_name": self.campaign_name,
            "objective": self.objective,
            "target_audience": self.target_audience,
            "core_message": self.core_message,
            "emotional_angle": self.emotional_angle,
            "rational_angle": self.rational_angle,
            "cta_strategy": self.cta_strategy,
            "platform_role": self.platform_role,
            "asset_role": self.asset_role,
            "content_sequence": self.content_sequence,
            "visual_direction": self.visual_direction,
            "governance_sensitivity_level": self.governance_sensitivity_level,
            "notes": self.notes,
        }


class CampaignStrategist:
    """Build a deterministic campaign strategy from request data."""

    def build(self, request: dict[str, Any]) -> dict[str, Any]:
        """Return a campaign strategy."""

        campaign_type = normalize_campaign_type(str(request.get("campaign_type", "")))
        contract = get_campaign_contract(campaign_type)
        brand = normalize_key(str(request.get("brand", "")))
        audience = normalize_key(str(request.get("audience", "")))
        location = normalize_key(str(request.get("location", "")))
        objective = str(request.get("objective", "")).strip()
        campaign_name = self._build_campaign_name(brand, campaign_type, location)
        core_message = self._build_core_message(request, contract)
        emotional_angle = self._build_emotional_angle(request, contract)
        rational_angle = self._build_rational_angle(request, contract)
        asset_role = self._build_asset_roles(contract)
        visual_direction = self._build_visual_direction(request, contract)
        sensitivity = self._sensitivity_level(campaign_type)
        return CampaignStrategy(
            campaign_type=campaign_type,
            campaign_name=campaign_name,
            objective=objective,
            target_audience=audience,
            core_message=core_message,
            emotional_angle=emotional_angle,
            rational_angle=rational_angle,
            cta_strategy=contract.cta_strategy,
            platform_role=PLATFORM_ROLE_MAP,
            asset_role=asset_role,
            content_sequence=contract.content_sequence,
            visual_direction=visual_direction,
            governance_sensitivity_level=sensitivity,
            notes=contract.notes + [f"Generated at {datetime.now(timezone.utc).isoformat()}"],
        ).to_dict()

    def _build_campaign_name(self, brand: str, campaign_type: str, location: str) -> str:
        parts = [part for part in (brand, campaign_type, location) if part]
        return "_".join(parts) if parts else "campaign_pack"

    def _build_core_message(self, request: dict[str, Any], contract: Any) -> str:
        objective = str(request.get("objective", "")).strip()
        location = str(request.get("location", "")).strip().replace("_", " ")
        audience = str(request.get("audience", "")).strip().replace("_", " ")
        campaign_type = normalize_campaign_type(str(request.get("campaign_type", "")))
        return " | ".join(
            part for part in [
                objective,
                audience,
                location,
                campaign_type.replace("_", " "),
                contract.cta_strategy,
            ]
            if part
        )

    def _build_emotional_angle(self, request: dict[str, Any], contract: Any) -> str:
        campaign_type = normalize_campaign_type(str(request.get("campaign_type", "")))
        mapping = {
            "property_launch": "fresh opportunity and lifestyle anticipation",
            "relocation_campaign": "calm transition and reassurance",
            "neighborhood_spotlight": "place identity and local discovery",
            "reform_opportunity": "potential, transformation, and practical optimism",
            "lifestyle_campaign": "aspiration and Mediterranean living",
            "investment_angle": "measured confidence and caution",
            "brand_awareness": "trust, familiarity, and service confidence",
        }
        return mapping.get(campaign_type, contract.cta_strategy)

    def _build_rational_angle(self, request: dict[str, Any], contract: Any) -> str:
        location = str(request.get("location", "")).strip().replace("_", " ")
        property_type = str(request.get("property_type", "")).strip().replace("_", " ")
        return " | ".join(part for part in [location, property_type, contract.cta_strategy] if part)

    def _build_asset_roles(self, contract: Any) -> dict[str, str]:
        roles: dict[str, str] = {}
        for index, asset in enumerate(contract.required_assets, start=1):
            roles[asset] = f"campaign asset {index}"
        return roles

    def _build_visual_direction(self, request: dict[str, Any], contract: Any) -> str:
        location = str(request.get("location", "")).replace("_", " ")
        property_type = str(request.get("property_type", "")).replace("_", " ")
        return " | ".join(part for part in [contract.cta_strategy, location, property_type] if part)

    def _sensitivity_level(self, campaign_type: str) -> str:
        if campaign_type in {"investment_angle", "reform_opportunity"}:
            return "high"
        if campaign_type in {"property_launch", "relocation_campaign", "brand_awareness"}:
            return "medium"
        return "medium"
