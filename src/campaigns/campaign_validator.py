"""Validation rules for composed campaign packs."""

from __future__ import annotations

from typing import Any

from src.campaigns.campaign_contracts import get_campaign_contract, list_supported_campaign_types
from src.campaigns.campaign_assets import ASSET_STATUSES
from src.utils.file_utils import normalize_key


class CampaignValidator:
    """Validate campaign request and composed campaign structures."""

    def validate_campaign_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Validate the campaign request payload."""

        warnings: list[str] = []
        errors: list[str] = []

        if not isinstance(request, dict):
            return {"valid": False, "warnings": [], "errors": ["Campaign request must be a dictionary."]}

        campaign_type = normalize_key(str(request.get("campaign_type", "")))
        if not campaign_type:
            errors.append("Missing campaign_type.")
        elif campaign_type not in list_supported_campaign_types():
            errors.append(f"Unsupported campaign_type: {campaign_type}")

        for field_name in ("brand", "objective", "audience"):
            if not str(request.get(field_name, "")).strip():
                errors.append(f"Missing {field_name}.")

        platforms = request.get("platforms", [])
        if not isinstance(platforms, list) or not platforms:
            warnings.append("Campaign platforms are missing or malformed.")

        assets_required = request.get("assets_required", [])
        if not isinstance(assets_required, list) or not assets_required:
            warnings.append("Campaign assets_required are missing or empty.")

        return {"valid": len(errors) == 0, "warnings": warnings, "errors": errors}

    def validate_campaign_pack(self, campaign_pack: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        """Validate a composed campaign pack."""

        warnings: list[str] = []
        errors: list[str] = []

        strategy = campaign_pack.get("strategy")
        if not isinstance(strategy, dict) or not strategy:
            errors.append("Campaign strategy is missing.")

        asset_plan = campaign_pack.get("asset_plan")
        if not isinstance(asset_plan, dict) or not asset_plan:
            errors.append("Campaign asset plan is missing.")

        sequence = campaign_pack.get("content_sequence")
        if not isinstance(sequence, list) or not sequence:
            errors.append("Campaign sequence is missing.")

        assets = campaign_pack.get("assets")
        if not isinstance(assets, dict):
            errors.append("Campaign assets payload is malformed.")
        else:
            for asset_key, asset_value in assets.items():
                status = str(asset_value.get("status", "")).lower() if isinstance(asset_value, dict) else "missing"
                if status not in ASSET_STATUSES:
                    warnings.append(f"Unknown asset status for {asset_key}: {status}")
                if status == "rejected":
                    errors.append(f"Rejected asset present: {asset_key}")

        if request.get("campaign_type"):
            contract = get_campaign_contract(str(request["campaign_type"]))
            required_assets = set(contract.required_assets)
            present_assets = {str(key) for key in (assets or {}).keys()}
            missing = sorted(required_assets - present_assets)
            if missing:
                warnings.append(f"Missing campaign assets: {', '.join(missing)}")

        return {"valid": len(errors) == 0, "warnings": warnings, "errors": errors}
