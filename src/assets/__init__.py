"""Asset coordination package."""

from src.assets.asset_coordinator import AssetCoordinator
from src.assets.asset_contracts import (
    ASSET_ALIASES,
    ASSET_CONTRACTS,
    AssetContract,
    get_asset_contract,
    list_supported_asset_types,
    normalize_asset_type,
)
from src.assets.asset_plan import AssetPlan, build_asset_plan
from src.assets.asset_requirements import (
    build_asset_requirements,
    get_asset_type_requirements,
    get_platform_requirements,
)
from src.assets.asset_result import AssetResult, build_asset_failure, build_asset_success
from src.assets.asset_validator import AssetValidator

__all__ = [
    "AssetCoordinator",
    "AssetContract",
    "AssetPlan",
    "AssetResult",
    "AssetValidator",
    "ASSET_ALIASES",
    "ASSET_CONTRACTS",
    "build_asset_failure",
    "build_asset_plan",
    "build_asset_requirements",
    "build_asset_success",
    "get_asset_contract",
    "get_asset_type_requirements",
    "get_platform_requirements",
    "list_supported_asset_types",
    "normalize_asset_type",
]
