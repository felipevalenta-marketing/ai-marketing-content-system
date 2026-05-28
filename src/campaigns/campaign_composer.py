"""Compose deterministic campaign packs from existing assets."""

from __future__ import annotations

from typing import Any

from src.campaigns.campaign_assets import normalize_campaign_assets
from src.campaigns.campaign_contracts import get_campaign_contract, list_supported_campaign_types, normalize_campaign_type
from src.campaigns.campaign_exporter import CampaignExporter
from src.campaigns.campaign_result import build_campaign_failure, build_campaign_success
from src.campaigns.campaign_strategy import CampaignStrategist
from src.campaigns.campaign_validator import CampaignValidator
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context, log_warning


class CampaignComposer:
    """Coordinate existing assets into a complete campaign pack."""

    def __init__(self, output_root: str = "outputs", logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.strategist = CampaignStrategist()
        self.validator = CampaignValidator()
        self.exporter = CampaignExporter(output_root=output_root, logger=self.logger)

    def compose(self, request: dict[str, Any], assets: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build a campaign pack from existing assets."""

        valid, reason = self.validate_campaign_request(request)
        normalized_request = self._normalize_request(request)
        if not valid:
            return build_campaign_failure(
                campaign_name=normalized_request.get("campaign_name", ""),
                campaign_type=normalized_request.get("campaign_type", ""),
                objective=normalized_request.get("objective", ""),
                brand=normalized_request.get("brand", ""),
                audience=normalized_request.get("audience", ""),
                location=normalized_request.get("location", ""),
                strategy={},
                asset_plan={},
                platform_plan={},
                content_sequence=[],
                governance_summary={"status": "rejected", "warnings": [], "errors": [reason or "Invalid campaign request."]},
                metadata={"request": normalized_request},
                warnings=[],
                errors=[reason or "Invalid campaign request."],
                assets={},
            )

        contract = get_campaign_contract(normalized_request["campaign_type"])
        normalized_request["assets_required"] = list(normalized_request.get("assets_required") or contract.required_assets)
        normalized_request["platforms"] = list(normalized_request.get("platforms") or list(contract.platform_plan.keys()))
        strategy = self.build_campaign_strategy(normalized_request)
        asset_plan = self.build_asset_plan(normalized_request)
        platform_plan = self.build_platform_plan(normalized_request)
        content_sequence = self.build_content_sequence(normalized_request)
        normalized_assets = self._merge_missing_assets(normalized_request, normalize_campaign_assets(assets))
        campaign_pack = self.assemble_campaign_pack(normalized_request, normalized_assets)
        governance_summary = self.summarize_governance(normalized_assets)
        validation_result = self.validator.validate_campaign_pack(campaign_pack, normalized_request)
        warnings = list(dict.fromkeys(validation_result["warnings"] + governance_summary.get("warnings", [])))
        errors = list(dict.fromkeys(validation_result["errors"] + governance_summary.get("errors", [])))

        if not validation_result["valid"]:
            log_warning(self.logger, f"Campaign validation issues: {errors}")

        export_paths: dict[str, str] = {}
        if normalized_request.get("enable_export"):
            export_paths = self.exporter.export(campaign_pack, normalized_request["brand"], campaign_pack["campaign_name"])

        if validation_result["valid"]:
            return build_campaign_success(
                campaign_name=campaign_pack["campaign_name"],
                campaign_type=normalized_request["campaign_type"],
                objective=normalized_request["objective"],
                brand=normalized_request["brand"],
                audience=normalized_request["audience"],
                location=normalized_request["location"],
                strategy=strategy,
                asset_plan=asset_plan,
                assets=normalized_assets,
                platform_plan=platform_plan,
                content_sequence=content_sequence,
                governance_summary=governance_summary,
                metadata={"request": normalized_request, "contract": get_campaign_contract(normalized_request["campaign_type"]).to_dict()},
                warnings=warnings,
                errors=[],
                export_paths=export_paths,
            )

        return build_campaign_failure(
            campaign_name=campaign_pack["campaign_name"],
            campaign_type=normalized_request["campaign_type"],
            objective=normalized_request["objective"],
            brand=normalized_request["brand"],
            audience=normalized_request["audience"],
            location=normalized_request["location"],
            strategy=strategy,
            asset_plan=asset_plan,
            platform_plan=platform_plan,
            content_sequence=content_sequence,
            governance_summary=governance_summary,
            metadata={"request": normalized_request, "contract": get_campaign_contract(normalized_request["campaign_type"]).to_dict()},
            warnings=warnings,
            errors=errors,
            export_paths=export_paths,
            assets=normalized_assets,
        )

    def validate_campaign_request(self, request: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate a campaign request."""

        result = self.validator.validate_campaign_request(request)
        if not result["valid"]:
            return False, "; ".join(result["errors"]) if result["errors"] else "Invalid campaign request."
        return True, None

    def build_campaign_strategy(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build the campaign strategy."""

        log_context(self.logger, "Building campaign strategy")
        return self.strategist.build(request)

    def build_asset_plan(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build the asset plan from the campaign contract."""

        contract = get_campaign_contract(str(request.get("campaign_type", "")))
        assets_required = list(contract.required_assets)
        additional_assets = [asset for asset in request.get("assets_required", []) if asset not in assets_required]
        platform_plan = self.build_platform_plan(request)
        return {
            "required_assets": assets_required,
            "additional_assets": additional_assets,
            "asset_roles": self.build_campaign_strategy(request).get("asset_role", {}),
            "platform_plan": platform_plan,
            "missing_assets": [],
        }

    def build_platform_plan(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build the platform plan from the campaign contract."""

        contract = get_campaign_contract(str(request.get("campaign_type", "")))
        return contract.platform_plan

    def build_content_sequence(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        """Build the campaign content sequence."""

        contract = get_campaign_contract(str(request.get("campaign_type", "")))
        sequence: list[dict[str, Any]] = []
        for step in contract.content_sequence:
            sequence.append(
                {
                    "step": step.get("step", ""),
                    "asset_type": step.get("asset_type", ""),
                    "platform": self._platform_for_asset(contract, step.get("asset_type", "")),
                    "purpose": self._purpose_for_step(step.get("step", ""), request),
                }
            )
        return sequence

    def assemble_campaign_pack(self, request: dict[str, Any], assets: dict[str, Any] | None = None) -> dict[str, Any]:
        """Assemble a campaign pack from request and assets."""

        normalized_request = self._normalize_request(request)
        strategy = self.build_campaign_strategy(normalized_request)
        asset_plan = self.build_asset_plan(normalized_request)
        platform_plan = self.build_platform_plan(normalized_request)
        content_sequence = self.build_content_sequence(normalized_request)
        campaign_name = strategy.get("campaign_name") or normalized_request.get("campaign_name") or self._build_campaign_name(normalized_request)
        governance_summary = self.summarize_governance(assets or {})
        return {
            "campaign_name": campaign_name,
            "campaign_type": normalized_request.get("campaign_type", ""),
            "objective": normalized_request.get("objective", ""),
            "brand": normalized_request.get("brand", ""),
            "audience": normalized_request.get("audience", ""),
            "location": normalized_request.get("location", ""),
            "strategy": strategy,
            "asset_plan": asset_plan,
            "assets": assets or {},
            "platform_plan": platform_plan,
            "content_sequence": content_sequence,
            "governance_summary": governance_summary,
            "metadata": {
                "request": normalized_request,
                "supported_campaign_types": list_supported_campaign_types(),
            },
            "warnings": governance_summary.get("warnings", []),
            "errors": governance_summary.get("errors", []),
        }

    def summarize_governance(self, assets: dict[str, Any]) -> dict[str, Any]:
        """Summarize governance findings from asset results."""

        approved = 0
        warnings = 0
        rejected = 0
        missing = 0
        critical_errors: list[str] = []
        asset_statuses: dict[str, str] = {}
        for asset_type, asset in (assets or {}).items():
            status = str(asset.get("status", "missing")).lower() if isinstance(asset, dict) else "missing"
            asset_statuses[asset_type] = status
            if status == "approved":
                approved += 1
            elif status == "warning":
                warnings += 1
            elif status == "rejected":
                rejected += 1
            else:
                missing += 1
            gov = asset.get("governance_result") if isinstance(asset, dict) else {}
            if isinstance(gov, dict):
                critical_errors.extend([err for err in gov.get("errors", []) if "critical" in str(err).lower() or "guaranteed" in str(err).lower() or "risk-free" in str(err).lower()])

        status = "approved"
        if rejected or critical_errors:
            status = "rejected"
        elif warnings or missing:
            status = "needs_review"
        return {
            "status": status,
            "approved_assets": approved,
            "warning_assets": warnings,
            "rejected_assets": rejected,
            "missing_assets": missing,
            "critical_errors": list(dict.fromkeys(critical_errors)),
            "asset_statuses": asset_statuses,
            "warnings": [f"{missing} asset(s) missing"] if missing else [],
            "errors": critical_errors,
        }

    def _normalize_request(self, request: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(request or {})
        normalized["brand"] = normalize_key(str(normalized.get("brand", "")))
        normalized["campaign_type"] = normalize_key(str(normalized.get("campaign_type", "")))
        normalized["objective"] = str(normalized.get("objective", "")).strip()
        normalized["audience"] = str(normalized.get("audience", "")).strip()
        normalized["location"] = normalize_key(str(normalized.get("location", "")))
        normalized["property_type"] = normalize_key(str(normalized.get("property_type", "")))
        normalized["campaign_name"] = str(normalized.get("campaign_name", "")).strip()
        normalized["platforms"] = list(normalized.get("platforms", [])) if isinstance(normalized.get("platforms"), list) else []
        normalized["assets_required"] = list(normalized.get("assets_required", [])) if isinstance(normalized.get("assets_required"), list) else []
        normalized["extra_notes"] = str(normalized.get("extra_notes", "")).strip()
        normalized["enable_export"] = bool(normalized.get("enable_export", False))
        return normalized

    def _build_campaign_name(self, request: dict[str, Any]) -> str:
        parts = [part for part in [request.get("brand"), request.get("campaign_type"), request.get("location")] if part]
        return "_".join(parts) if parts else "campaign_pack"

    def _platform_for_asset(self, contract: Any, asset_type: str) -> str:
        for platform, assets in contract.platform_plan.items():
            if asset_type in assets:
                return platform
        return "instagram"

    def _purpose_for_step(self, step: str, request: dict[str, Any]) -> str:
        objective = request.get("objective", "")
        return f"{step} for {objective}" if objective else step

    def _asset_status(self, asset: dict[str, Any]) -> str:
        status = str(asset.get("status", "missing")).lower()
        if status in {"approved", "warning", "rejected", "missing"}:
            return status
        return "missing"

    def _campaign_warning(self, message: str) -> str:
        return message

    def _build_missing_asset(self, asset_type: str, platform: str) -> dict[str, Any]:
        return {
            "asset_type": asset_type,
            "platform": platform,
            "purpose": "",
            "content": {},
            "formatted_output": {},
            "platform_variant": {},
            "governance_result": {},
            "metadata": {},
            "status": "missing",
        }

    def _merge_missing_assets(self, request: dict[str, Any], assets: dict[str, Any]) -> dict[str, Any]:
        contract = get_campaign_contract(request.get("campaign_type", ""))
        merged = dict(assets)
        for asset_type in contract.required_assets:
            if asset_type not in merged:
                merged[asset_type] = self._build_missing_asset(asset_type, self._platform_for_asset(contract, asset_type))
        return merged


if __name__ == "__main__":
    composer = CampaignComposer()
    sample_request = {
        "brand": "wenzel_partner",
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "property_type": "rustic_home",
        "platforms": ["instagram", "facebook", "linkedin", "email"],
        "assets_required": ["instagram_post", "instagram_reel", "image_prompt", "email_teaser", "linkedin_post"],
        "extra_notes": "Rustic exterior, modern comfort inside, close to Manacor and beaches.",
    }
    print("Campaign contract:")
    print(get_campaign_contract("property_launch").to_dict())
    print("Campaign strategy:")
    print(composer.build_campaign_strategy(sample_request))
    print("Campaign asset plan:")
    print(composer.build_asset_plan(sample_request))
    print("Campaign sequence:")
    print(composer.build_content_sequence(sample_request))
    print("Governance summary:")
    print(composer.summarize_governance({}))
    print("Composed pack with export disabled:")
    print(composer.compose(sample_request, assets={}))
