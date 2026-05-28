"""Asset generation coordination layer."""

from __future__ import annotations

from typing import Any

from src.assets.asset_exporter import AssetExporter
from src.assets.asset_contracts import list_supported_asset_types, normalize_asset_type
from src.assets.asset_plan import build_asset_plan
from src.assets.asset_requirements import build_asset_requirements
from src.assets.asset_result import build_asset_failure, build_asset_success
from src.assets.asset_validator import AssetValidator
from src.campaigns.campaign_contracts import get_campaign_contract, normalize_campaign_type
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context, log_warning


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
        existing_assets = self._extract_actual_assets(normalized_request)
        if normalized_request.get("image_prompt_result"):
            existing_assets["image_prompt"] = self._merge_image_prompt_result(
                existing_assets.get("image_prompt"),
                normalized_request.get("image_prompt_result"),
            )
        if normalized_request.get("video_script_result"):
            existing_assets["reel_script"] = self._merge_video_script_result(
                existing_assets.get("reel_script"),
                normalized_request.get("video_script_result"),
            )
        asset_bundle = self.assemble_asset_bundle(normalized_request, existing_assets=existing_assets)
        validation_result = self.validator.validate(normalized_request, asset_plan, asset_requirements, existing_assets)
        planned_assets = list(validation_result.get("planned_assets", []))
        existing_asset_names = list(validation_result.get("existing_assets", []))
        invalid_assets = list(validation_result.get("invalid_assets", []))
        missing_assets = list(validation_result.get("missing_assets", []))

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
                "assets": existing_assets,
                "video_script_result": normalized_request.get("video_script_result", {}),
                "planned_assets": planned_assets,
                "existing_assets": existing_asset_names,
                "missing_assets": missing_assets,
                "invalid_assets": invalid_assets,
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
                assets=existing_assets,
                planned_assets=planned_assets,
                existing_assets=existing_asset_names,
                missing_assets=missing_assets,
                invalid_assets=invalid_assets,
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
            assets=existing_assets,
            planned_assets=planned_assets,
            existing_assets=existing_asset_names,
            missing_assets=missing_assets,
            invalid_assets=invalid_assets,
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
        plan = build_asset_plan(request)
        return self._attach_creative_guidance(plan, request)

    def build_asset_requirements(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build the asset requirements."""

        log_context(self.logger, "Building asset requirements")
        requirements = build_asset_requirements(request)
        creative_guidance = self._extract_creative_guidance(request)
        if creative_guidance:
            requirements["creative_direction"] = creative_guidance
        return requirements

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
        if normalized_request.get("image_prompt_result"):
            assets["image_prompt"] = self._merge_image_prompt_result(
                assets.get("image_prompt"),
                normalized_request.get("image_prompt_result"),
            )
        if normalized_request.get("video_script_result"):
            assets["reel_script"] = self._merge_video_script_result(
                assets.get("reel_script"),
                normalized_request.get("video_script_result"),
            )
        missing_assets = self.summarize_missing_assets(asset_plan, existing_assets=assets)
        bundle = {
            "campaign_name": normalized_request.get("campaign_name") or self._build_campaign_name(normalized_request),
            "brand": normalized_request["brand"],
            "campaign_type": normalized_request["campaign_type"],
            "objective": normalized_request["objective"],
            "asset_plan": asset_plan,
            "asset_requirements": asset_requirements,
            "assets": assets,
            "image_prompt_result": normalized_request.get("image_prompt_result", {}),
            "video_script_result": normalized_request.get("video_script_result", {}),
            "creative_direction_result": normalized_request.get("creative_direction_result", {}),
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
        missing_assets: list[str] = []
        for asset in required_assets:
            canonical = normalize_asset_type(str(asset))
            entry = (existing_assets or {}).get(canonical)
            if entry is None:
                missing_assets.append(canonical)
                continue
            if isinstance(entry, dict) and str(entry.get("status", "missing")).lower() == "missing":
                missing_assets.append(canonical)
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
        normalized["assets_required"] = self._requested_assets(normalized)
        normalized["creative_direction"] = str(normalized.get("creative_direction", "")).strip()
        normalized["creative_direction_result"] = dict(normalized.get("creative_direction_result", {})) if isinstance(normalized.get("creative_direction_result"), dict) else {}
        normalized["visual_style"] = str(normalized.get("visual_style", "")).strip()
        normalized["image_type"] = str(normalized.get("image_type", "")).strip()
        normalized["aspect_ratio"] = str(normalized.get("aspect_ratio", "")).strip()
        normalized["image_prompt_result"] = dict(normalized.get("image_prompt_result", {})) if isinstance(normalized.get("image_prompt_result"), dict) else {}
        normalized["video_script_result"] = dict(normalized.get("video_script_result", {})) if isinstance(normalized.get("video_script_result"), dict) else {}
        normalized["extra_notes"] = str(normalized.get("extra_notes", "")).strip()
        normalized["enable_export"] = bool(normalized.get("enable_export", False))
        return normalized

    def _requested_assets(self, request: dict[str, Any]) -> list[str]:
        """Collect requested assets from all supported request locations."""

        assets_required = request.get("assets_required")
        if isinstance(assets_required, list) and assets_required:
            return [normalize_asset_type(str(asset)) for asset in assets_required if str(asset).strip()]

        asset_plan = request.get("asset_plan")
        if isinstance(asset_plan, dict):
            required_assets = asset_plan.get("required_assets", [])
            if isinstance(required_assets, list) and required_assets:
                return [normalize_asset_type(str(asset)) for asset in required_assets if str(asset).strip()]

        asset_requirements = request.get("asset_requirements")
        if isinstance(asset_requirements, dict) and asset_requirements:
            return [normalize_asset_type(str(asset_type)) for asset_type in asset_requirements.keys() if str(asset_type).strip()]

        return []

    def _extract_actual_assets(self, request: dict[str, Any]) -> dict[str, Any]:
        """Extract only real asset entries and ignore bundle metadata keys."""

        candidates: dict[str, Any] = {}
        for key in ("assets", "campaign_assets", "asset_bundle"):
            value = request.get(key)
            if isinstance(value, dict):
                candidates.update(value)

        if not candidates:
            return {}

        actual_assets: dict[str, Any] = {}
        for asset_type, payload in candidates.items():
            canonical = normalize_asset_type(str(asset_type))
            if asset_type in IGNORED_BUNDLE_KEYS:
                continue
            if canonical in IGNORED_BUNDLE_KEYS:
                continue
            if canonical not in list_supported_asset_types():
                continue
            if not isinstance(payload, dict):
                continue
            actual_assets[canonical] = dict(payload)
        return actual_assets

    def _normalize_existing_assets(self, assets: dict[str, Any]) -> dict[str, Any]:
        """Normalize existing assets into a deterministic bundle."""

        normalized: dict[str, Any] = {}
        for asset_type, payload in assets.items():
            if not isinstance(payload, dict):
                continue
            canonical = normalize_asset_type(str(asset_type))
            if canonical in IGNORED_BUNDLE_KEYS:
                continue
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
            "image_type": request.get("image_type", ""),
            "aspect_ratio": request.get("aspect_ratio", ""),
            "extra_notes": request.get("extra_notes", ""),
            "campaign_result_present": bool(request.get("campaign_result")),
            "campaign_strategy_present": bool(request.get("campaign_strategy")),
            "campaign_assets_present": bool(request.get("campaign_assets")),
            "image_prompt_result_present": bool(request.get("image_prompt_result")),
            "video_script_result_present": bool(request.get("video_script_result")),
            "creative_direction_result_present": bool(request.get("creative_direction_result")),
            "campaign_metadata": campaign_metadata,
        }
        if contract is not None:
            metadata["contract"] = contract
        return metadata

    def _attach_creative_guidance(self, plan: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        """Attach creative direction guidance to the asset plan."""

        creative_guidance = self._extract_creative_guidance(request)
        if not creative_guidance:
            return plan
        enriched = dict(plan)
        enriched["creative_direction_guidance"] = {
            "visual_identity": creative_guidance.get("visual_identity", {}),
            "moodboard": creative_guidance.get("moodboard", {}),
            "color_palette": creative_guidance.get("color_palette", {}),
            "lighting_direction": creative_guidance.get("lighting_direction", ""),
            "camera_style": creative_guidance.get("camera_style", ""),
            "platform_guidelines": creative_guidance.get("platform_guidelines", {}),
            "media_guidelines": creative_guidance.get("media_guidelines", {}),
        }
        return enriched

    def _extract_creative_guidance(self, request: dict[str, Any]) -> dict[str, Any]:
        """Safely extract creative direction guidance if present."""

        guidance = request.get("creative_direction_result", {})
        return dict(guidance) if isinstance(guidance, dict) else {}

    def _merge_image_prompt_result(self, asset: dict[str, Any] | None, image_prompt_result: dict[str, Any]) -> dict[str, Any]:
        """Attach enhanced image prompt output to an image asset entry."""

        merged = dict(asset or {})
        if not isinstance(image_prompt_result, dict):
            return merged
        merged.setdefault("asset_type", "image_prompt")
        merged.setdefault("platform", image_prompt_result.get("platform", ""))
        merged.setdefault("purpose", "")
        merged["image_prompt_result"] = dict(image_prompt_result)
        merged["subject"] = image_prompt_result.get("metadata", {}).get("image_type", "") if isinstance(image_prompt_result.get("metadata"), dict) else ""
        merged["composition"] = image_prompt_result.get("composition_style", "")
        merged["lighting"] = image_prompt_result.get("lighting_style", "")
        merged["style"] = image_prompt_result.get("visual_style", "")
        merged["aspect_ratio"] = image_prompt_result.get("aspect_ratio", "")
        merged["negative_prompt"] = image_prompt_result.get("negative_prompt", "")
        merged["platform_use"] = image_prompt_result.get("platform", "")
        merged["visual_direction"] = image_prompt_result.get("prompt", "")
        merged["enhanced_image_prompt"] = image_prompt_result.get("prompt", "")
        merged["visual_style"] = image_prompt_result.get("visual_style", "")
        merged["lighting_style"] = image_prompt_result.get("lighting_style", "")
        merged["composition_style"] = image_prompt_result.get("composition_style", "")
        merged["camera_direction"] = image_prompt_result.get("camera_direction", "")
        merged["validation"] = image_prompt_result.get("validation", {})
        merged["metadata"] = {
            **(dict(merged.get("metadata", {})) if isinstance(merged.get("metadata"), dict) else {}),
            "image_prompt_result": image_prompt_result.get("metadata", {}),
        }
        if not merged.get("status"):
            merged["status"] = "approved" if image_prompt_result.get("success") else "warning"
        return merged

    def _merge_video_script_result(self, asset: dict[str, Any] | None, video_script_result: dict[str, Any]) -> dict[str, Any]:
        """Attach structured video script output to a reel script asset entry."""

        merged = dict(asset or {})
        if not isinstance(video_script_result, dict):
            return merged
        merged.setdefault("asset_type", "reel_script")
        merged.setdefault("platform", video_script_result.get("platform", ""))
        merged.setdefault("purpose", "")
        scene_sequence = list(video_script_result.get("scene_sequence", [])) if isinstance(video_script_result.get("scene_sequence"), list) else []
        storyboard = list(video_script_result.get("storyboard", [])) if isinstance(video_script_result.get("storyboard"), list) else []
        merged["video_script_result"] = dict(video_script_result)
        merged["hook"] = video_script_result.get("hook", "")
        merged["script"] = video_script_result.get("script", "")
        merged["scenes"] = scene_sequence
        merged["storyboard"] = storyboard
        merged["voiceover_direction"] = video_script_result.get("voiceover", "")
        merged["cta"] = video_script_result.get("cta", "")
        merged["visual_direction"] = video_script_result.get("script", "") or video_script_result.get("hook", "")
        merged["duration"] = video_script_result.get("duration", "")
        merged["camera_direction"] = video_script_result.get("camera_direction", "")
        merged["music_mood"] = video_script_result.get("music_mood", "")
        merged["metadata"] = {
            **(dict(merged.get("metadata", {})) if isinstance(merged.get("metadata"), dict) else {}),
            "video_script_result": video_script_result.get("metadata", {}),
        }
        if not merged.get("status"):
            merged["status"] = "approved" if video_script_result.get("success") else "warning"
        return merged

    def build_analytics_snapshot(self, asset_result: dict[str, Any]) -> dict[str, Any]:
        """Build a safe asset analytics snapshot."""

        assets = asset_result.get("assets", {})
        missing_assets = asset_result.get("missing_assets", [])
        validation_result = asset_result.get("validation_result", {})
        return {
            "brand": asset_result.get("brand", ""),
            "campaign_type": asset_result.get("campaign_type", ""),
            "objective": asset_result.get("objective", ""),
            "asset_count": len(assets) if isinstance(assets, dict) else 0,
            "missing_asset_count": len(missing_assets) if isinstance(missing_assets, list) else 0,
            "validation_valid": bool(validation_result.get("valid", False)) if isinstance(validation_result, dict) else False,
            "warning_count": len(asset_result.get("warnings", []) or []),
            "error_count": len(asset_result.get("errors", []) or []),
        }


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
