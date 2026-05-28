"""Asset generation coordination layer."""

from __future__ import annotations

from typing import Any

from src.assets.asset_exporter import AssetExporter
from src.assets.asset_contracts import normalize_asset_type
from src.assets.asset_plan import build_asset_plan
from src.assets.asset_requirements import build_asset_requirements
from src.assets.asset_result import build_asset_failure, build_asset_success
from src.assets.asset_validator import AssetValidator
from src.campaigns.campaign_contracts import get_campaign_contract, normalize_campaign_type
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context, log_warning


class AssetCoordinator:
    """Coordinate asset planning, validation, and export-ready packaging."""

    def __init__(self, output_root: str = "outputs", logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.validator = AssetValidator()
        self.exporter = AssetExporter(output_root=output_root, logger=self.logger)

    def coordinate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Coordinate asset requirements and bundle planning."""

        valid, reason = self.validate_asset_request(request)
        normalized_request = self._normalize_request(request)
        log_context(self.logger, f"Coordinating assets for {normalized_request['brand']}/{normalized_request['campaign_type']}")

        asset_plan = self.build_asset_plan(normalized_request)
        asset_requirements = self.build_asset_requirements(normalized_request)
        existing_assets = self._extract_existing_assets(normalized_request)
        assets = self.assemble_asset_bundle(normalized_request, existing_assets=existing_assets)
        missing_assets = self.summarize_missing_assets(asset_plan, existing_assets=existing_assets)
        validation_result = self.validator.validate(normalized_request, asset_plan, asset_requirements, assets)

        warnings = list(dict.fromkeys(validation_result["warnings"]))
        errors = list(dict.fromkeys(validation_result["errors"]))
        if not valid:
            errors.append(reason or "Invalid asset request.")
        export_paths: dict[str, str] = {}
        if normalized_request.get("enable_export"):
            export_paths = self.exporter.export(
                {
                    "brand": normalized_request["brand"],
                    "campaign_type": normalized_request["campaign_type"],
                    "objective": normalized_request["objective"],
                    "asset_plan": asset_plan,
                    "asset_requirements": asset_requirements,
                    "assets": assets,
                    "missing_assets": missing_assets,
                    "validation_result": validation_result,
                    "metadata": self._build_metadata(normalized_request),
                    "warnings": warnings,
                    "errors": errors,
                },
                normalized_request["brand"],
                normalized_request["campaign_type"],
            )

        success = validation_result["valid"] and valid
        if success:
            return build_asset_success(
                brand=normalized_request["brand"],
                campaign_type=normalized_request["campaign_type"],
                objective=normalized_request["objective"],
                asset_plan=asset_plan,
                asset_requirements=asset_requirements,
                assets=assets,
                missing_assets=missing_assets,
                validation_result=validation_result,
                metadata=self._build_metadata(normalized_request),
                warnings=warnings,
                errors=[],
                export_paths=export_paths,
            )

        log_warning(self.logger, f"Asset coordination needs attention for {normalized_request['brand']}/{normalized_request['campaign_type']}")
        return build_asset_failure(
            brand=normalized_request["brand"],
            campaign_type=normalized_request["campaign_type"],
            objective=normalized_request["objective"],
            asset_plan=asset_plan,
            asset_requirements=asset_requirements,
            assets=assets,
            missing_assets=missing_assets,
            validation_result=validation_result,
            metadata=self._build_metadata(normalized_request),
            warnings=warnings,
            errors=errors,
            export_paths=export_paths,
        )

    def validate_asset_request(self, request: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate an asset request."""

        result = self.validator.validate_asset_request(request)
        if not result["valid"]:
            return False, "; ".join(result["errors"]) if result["errors"] else "Invalid asset request."
        return True, None

    def build_asset_plan(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build the asset plan."""

        log_context(self.logger, "Building asset plan")
        return build_asset_plan(request)

    def build_asset_requirements(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build the asset requirements."""

        log_context(self.logger, "Building asset requirements")
        return build_asset_requirements(request)

    def map_assets_to_platforms(self, request: dict[str, Any]) -> dict[str, list[str]]:
        """Map requested assets to target platforms."""

        plan = self.build_asset_plan(request)
        return dict(plan.get("platform_mapping", {}))

    def assemble_asset_bundle(self, request: dict[str, Any], existing_assets: dict[str, Any] | None = None) -> dict[str, Any]:
        """Assemble a coordinated asset bundle."""

        normalized_request = self._normalize_request(request)
        asset_plan = self.build_asset_plan(normalized_request)
        asset_requirements = self.build_asset_requirements(normalized_request)
        contract = get_campaign_contract(normalized_request["campaign_type"])
        assets = self._normalize_existing_assets(existing_assets or {})
        if not assets and normalized_request.get("campaign_assets"):
            assets = self._normalize_existing_assets(normalized_request.get("campaign_assets", {}))
        missing_assets = self.summarize_missing_assets(asset_plan, existing_assets=assets)
        bundle = {
            "campaign_name": normalized_request.get("campaign_name") or self._build_campaign_name(normalized_request),
            "brand": normalized_request["brand"],
            "campaign_type": normalized_request["campaign_type"],
            "objective": normalized_request["objective"],
            "asset_plan": asset_plan,
            "asset_requirements": asset_requirements,
            "assets": assets,
            "missing_assets": missing_assets,
            "platform_mapping": self.map_assets_to_platforms(normalized_request),
            "governance_summary": self._build_governance_summary(normalized_request, assets),
            "metadata": self._build_metadata(normalized_request, contract.to_dict()),
            "warnings": [],
            "errors": [],
            "status": "ready" if not missing_assets else "needs_review",
        }
        return bundle

    def summarize_missing_assets(self, asset_plan: dict[str, Any], existing_assets: dict[str, Any] | None = None) -> list[str]:
        """Summarize missing assets based on the plan and existing assets."""

        required_assets = list(asset_plan.get("required_assets", []))
        existing_keys = {normalize_asset_type(str(asset_type)) for asset_type in (existing_assets or {}).keys()}
        missing_assets = [asset for asset in required_assets if asset not in existing_keys]
        return sorted(list(dict.fromkeys(missing_assets)))

    def _normalize_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Normalize asset request values."""

        normalized = dict(request or {})
        normalized["brand"] = normalize_key(str(normalized.get("brand", "")))
        normalized["campaign_type"] = normalize_campaign_type(str(normalized.get("campaign_type") or normalized.get("content_type") or "asset_bundle"))
        normalized["objective"] = str(normalized.get("objective", "")).strip()
        normalized["audience"] = str(normalized.get("audience", "")).strip()
        normalized["location"] = normalize_key(str(normalized.get("location", "")))
        normalized["property_type"] = normalize_key(str(normalized.get("property_type", "")))
        normalized["campaign_name"] = str(normalized.get("campaign_name", "")).strip()
        normalized["platforms"] = list(normalized.get("platforms", [])) if isinstance(normalized.get("platforms"), list) else []
        normalized["assets_required"] = list(normalized.get("assets_required", [])) if isinstance(normalized.get("assets_required"), list) else []
        normalized["creative_direction"] = str(normalized.get("creative_direction", "")).strip()
        normalized["visual_style"] = str(normalized.get("visual_style", "")).strip()
        normalized["extra_notes"] = str(normalized.get("extra_notes", "")).strip()
        normalized["enable_export"] = bool(normalized.get("enable_export", False))
        return normalized

    def _extract_existing_assets(self, request: dict[str, Any]) -> dict[str, Any]:
        """Extract existing assets from a request payload."""

        for key in ("campaign_assets", "assets", "asset_bundle"):
            value = request.get(key)
            if isinstance(value, dict):
                return value
        return {}

    def _normalize_existing_assets(self, assets: dict[str, Any]) -> dict[str, Any]:
        """Normalize existing assets into a deterministic bundle."""

        normalized: dict[str, Any] = {}
        for asset_type, payload in assets.items():
            if not isinstance(payload, dict):
                continue
            canonical = normalize_asset_type(str(asset_type))
            normalized[canonical] = dict(payload)
        return normalized

    def _build_campaign_name(self, request: dict[str, Any]) -> str:
        """Build a deterministic campaign name."""

        parts = [part for part in [request.get("brand"), request.get("campaign_type"), request.get("location")] if part]
        return "_".join(parts) if parts else "campaign_pack"

    def _build_governance_summary(self, request: dict[str, Any], assets: dict[str, Any]) -> dict[str, Any]:
        """Build a lightweight governance summary for asset coordination."""

        statuses = [str(asset.get("status", "missing")).lower() for asset in assets.values() if isinstance(asset, dict)]
        missing = statuses.count("missing")
        rejected = statuses.count("rejected")
        warnings = statuses.count("warning")
        status = "ready"
        if rejected:
            status = "rejected"
        elif missing or warnings:
            status = "needs_review"
        return {
            "status": status,
            "approved_assets": statuses.count("approved"),
            "warning_assets": warnings,
            "rejected_assets": rejected,
            "missing_assets": missing,
            "campaign_type": request.get("campaign_type", ""),
        }

    def _build_metadata(self, request: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build safe metadata for exports and reporting."""

        campaign_metadata = request.get("campaign_metadata", {})
        if not isinstance(campaign_metadata, dict):
            campaign_metadata = {}
        metadata = {
            "brand": request.get("brand", ""),
            "campaign_type": request.get("campaign_type", ""),
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "platforms": request.get("platforms", []),
            "assets_required": request.get("assets_required", []),
            "creative_direction": request.get("creative_direction", ""),
            "visual_style": request.get("visual_style", ""),
            "extra_notes": request.get("extra_notes", ""),
            "campaign_result_present": bool(request.get("campaign_result")),
            "campaign_strategy_present": bool(request.get("campaign_strategy")),
            "campaign_assets_present": bool(request.get("campaign_assets")),
            "campaign_metadata": campaign_metadata,
        }
        if contract is not None:
            metadata["contract"] = contract
        return metadata


if __name__ == "__main__":
    coordinator = AssetCoordinator()
    sample_request = {
        "brand": "wenzel_partner",
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
    print("Asset request valid:", coordinator.validate_asset_request(sample_request))
    print("Asset plan:")
    print(coordinator.build_asset_plan(sample_request))
    print("Asset requirements:")
    print(coordinator.build_asset_requirements(sample_request))
    print("Missing assets:")
    print(coordinator.summarize_missing_assets(coordinator.build_asset_plan(sample_request), existing_assets={}))
    print("Asset bundle:")
    print(coordinator.coordinate(sample_request))
