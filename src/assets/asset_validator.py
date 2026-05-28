"""Validation helpers for asset coordination requests and plans."""

from __future__ import annotations

from typing import Any

from src.assets.asset_contracts import get_asset_contract, list_supported_asset_types, normalize_asset_type
from src.assets.asset_requirements import get_asset_type_requirements
from src.utils.file_utils import normalize_key


IGNORED_BUNDLE_KEYS = {
    "campaign_name",
    "brand",
    "campaign_type",
    "objective",
    "asset_plan",
    "asset_requirements",
    "assets",
    "missing_assets",
    "platform_mapping",
    "governance_summary",
    "metadata",
    "warnings",
    "errors",
    "status",
}


class AssetValidator:
    """Validate asset coordination requests and generated bundles."""

    def validate(self, request: dict[str, Any], asset_plan: dict[str, Any], asset_requirements: dict[str, Any], assets: dict[str, Any]) -> dict[str, Any]:
        """Validate the full asset coordination state."""

        valid, warnings, errors = True, [], []
        request_result = self.validate_asset_request(request)
        warnings.extend(request_result["warnings"])
        errors.extend(request_result["errors"])
        if not request_result["valid"]:
            valid = False
        plan_result = self.validate_asset_plan(asset_plan)
        warnings.extend(plan_result["warnings"])
        errors.extend(plan_result["errors"])
        if not plan_result["valid"]:
            valid = False
        bundle_result = self.validate_asset_bundle(assets, asset_plan, asset_requirements)
        warnings.extend(bundle_result["warnings"])
        errors.extend(bundle_result["errors"])
        if not bundle_result["valid"]:
            valid = False
        return {"valid": valid, "warnings": list(dict.fromkeys(warnings)), "errors": list(dict.fromkeys(errors))}

    def validate_asset_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Validate the incoming asset request."""

        warnings: list[str] = []
        errors: list[str] = []
        if not isinstance(request, dict):
            return {"valid": False, "warnings": [], "errors": ["Asset request must be a dictionary."]}

        brand = normalize_key(str(request.get("brand", "")))
        objective = str(request.get("objective", "")).strip()
        platforms = request.get("platforms", [])
        assets_required = request.get("assets_required", [])
        campaign_type = normalize_key(str(request.get("campaign_type", "")))

        if not brand:
            errors.append("Missing brand.")
        if not objective:
            errors.append("Missing objective.")
        if not campaign_type:
            warnings.append("Missing campaign_type; a generic asset bundle context will be used.")
        if not isinstance(platforms, list) or not platforms:
            errors.append("Missing platforms.")
        if not isinstance(assets_required, list) or not assets_required:
            errors.append("Missing assets_required.")
        else:
            for asset_type in assets_required:
                canonical = normalize_asset_type(str(asset_type))
                if canonical not in list_supported_asset_types():
                    warnings.append(f"Unsupported asset type skipped: {asset_type}")

        if not str(request.get("creative_direction", "")).strip():
            warnings.append("Missing creative_direction; asset coordination will be less specific.")

        return {"valid": not errors, "warnings": list(dict.fromkeys(warnings)), "errors": list(dict.fromkeys(errors))}

    def validate_asset_plan(self, asset_plan: dict[str, Any]) -> dict[str, Any]:
        """Validate an asset plan structure."""

        warnings: list[str] = []
        errors: list[str] = []
        if not isinstance(asset_plan, dict):
            return {"valid": False, "warnings": [], "errors": ["Asset plan must be a dictionary."]}
        if not asset_plan.get("required_assets"):
            warnings.append("Asset plan does not include required_assets.")
        if not isinstance(asset_plan.get("platform_mapping", {}), dict):
            errors.append("Asset plan platform_mapping must be a dictionary.")
        if not isinstance(asset_plan.get("priority", {}), dict):
            errors.append("Asset plan priority must be a dictionary.")
        if not isinstance(asset_plan.get("dependencies", {}), dict):
            errors.append("Asset plan dependencies must be a dictionary.")
        return {"valid": not errors, "warnings": warnings, "errors": errors}

    def validate_asset_bundle(self, assets: dict[str, Any], asset_plan: dict[str, Any], asset_requirements: dict[str, Any]) -> dict[str, Any]:
        """Validate an asset bundle against the plan and requirements."""

        warnings: list[str] = []
        errors: list[str] = []
        planned_assets: list[str] = []
        existing_assets: list[str] = []
        invalid_assets: list[str] = []
        if not isinstance(assets, dict):
            return {
                "valid": False,
                "warnings": [],
                "errors": ["Assets bundle must be a dictionary."],
                "planned_assets": [],
                "existing_assets": [],
                "invalid_assets": [],
                "missing_assets": [],
            }

        asset_entries = self._extract_asset_entries(assets)
        required_assets = list(asset_plan.get("required_assets", []))
        missing_assets: list[str] = []

        for asset_type, payload in asset_entries.items():
            canonical = normalize_asset_type(asset_type)
            if canonical not in list_supported_asset_types():
                continue
            contract = get_asset_contract(canonical)
            requirements = get_asset_type_requirements(canonical)
            if not isinstance(payload, dict):
                errors.append(f"Asset {asset_type} must be a dictionary.")
                invalid_assets.append(canonical)
                continue
            normalized_payload = self._normalize_asset_payload(payload)
            if self._is_missing_asset(payload) or self._is_missing_asset(normalized_payload):
                if canonical in required_assets:
                    planned_assets.append(canonical)
                    missing_assets.append(canonical)
                continue
            existing_assets.append(canonical)
            for field_name in requirements.get("required_fields", contract.required_fields):
                if not self._is_non_empty(normalized_payload.get(field_name)):
                    if field_name in contract.required_fields:
                        warnings.append(f"Asset {asset_type} is missing required field: {field_name}")
                        if canonical not in invalid_assets:
                            invalid_assets.append(canonical)
                    else:
                        warnings.append(f"Asset {asset_type} is missing field: {field_name}")
            if canonical == "image_prompt" and not all(self._is_non_empty(normalized_payload.get(field)) for field in ("subject", "composition", "lighting", "style")):
                warnings.append("Image prompt is incomplete.")
                if canonical not in invalid_assets:
                    invalid_assets.append(canonical)
            if canonical == "video_prompt" and not all(self._is_non_empty(normalized_payload.get(field)) for field in ("scene_description", "camera_motion", "sequence", "mood")):
                warnings.append("Video prompt is incomplete.")
                if canonical not in invalid_assets:
                    invalid_assets.append(canonical)

        for asset in required_assets:
            canonical = normalize_asset_type(str(asset))
            if canonical not in asset_entries:
                missing_assets.append(canonical)

        if missing_assets:
            warnings.append("Some planned assets are missing and should be generated before export.")

        campaign_alignment = asset_requirements.get("campaign_alignment", {})
        if isinstance(campaign_alignment, dict) and not campaign_alignment.get("objective"):
            warnings.append("Asset requirements do not include campaign objective.")
        return {
            "valid": not errors,
            "warnings": list(dict.fromkeys(warnings)),
            "errors": list(dict.fromkeys(errors)),
            "planned_assets": list(dict.fromkeys(planned_assets)),
            "existing_assets": list(dict.fromkeys(existing_assets)),
            "invalid_assets": list(dict.fromkeys(invalid_assets)),
            "missing_assets": list(dict.fromkeys(missing_assets)),
        }

    def _extract_asset_entries(self, assets: dict[str, Any]) -> dict[str, Any]:
        """Return only real asset entries from a bundle-like payload."""

        extracted: dict[str, Any] = {}
        for asset_type, payload in assets.items():
            canonical = normalize_asset_type(str(asset_type))
            if asset_type in IGNORED_BUNDLE_KEYS or canonical in IGNORED_BUNDLE_KEYS:
                continue
            if canonical not in list_supported_asset_types():
                continue
            if not isinstance(payload, dict):
                continue
            extracted[canonical] = payload
        return extracted

    def _normalize_asset_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return the innermost creative payload for validation."""

        if not isinstance(payload, dict):
            return {}
        for key in ("formatted_output", "content"):
            nested = payload.get(key)
            if isinstance(nested, dict) and nested:
                return nested
        return payload

    def _is_non_empty(self, value: Any) -> bool:
        """Return whether a value contains meaningful content."""

        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, list):
            return bool(value)
        if isinstance(value, dict):
            return bool(value)
        return True

    def _is_missing_asset(self, asset: Any) -> bool:
        """Return whether an asset entry should be considered missing."""

        if not isinstance(asset, dict):
            return True
        return str(asset.get("status", "missing")).lower() == "missing"
