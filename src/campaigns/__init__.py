"""Campaign composition layer for packaging validated marketing assets."""

from src.campaigns.campaign_assets import CampaignAsset, normalize_campaign_assets
from src.campaigns.campaign_composer import CampaignComposer
from src.campaigns.campaign_contracts import CampaignContract, get_campaign_contract, list_supported_campaign_types
from src.campaigns.campaign_exporter import CampaignExporter
from src.campaigns.campaign_result import CampaignResult, build_campaign_failure, build_campaign_success
from src.campaigns.campaign_strategy import CampaignStrategy, CampaignStrategist
from src.campaigns.campaign_validator import CampaignValidator

__all__ = [
    "CampaignAsset",
    "CampaignComposer",
    "CampaignContract",
    "CampaignExporter",
    "CampaignResult",
    "CampaignStrategy",
    "CampaignStrategist",
    "CampaignValidator",
    "build_campaign_failure",
    "build_campaign_success",
    "get_campaign_contract",
    "list_supported_campaign_types",
    "normalize_campaign_assets",
]
