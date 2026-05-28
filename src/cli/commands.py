"""Command handlers for the AI Marketing Content System CLI."""

from __future__ import annotations

from dataclasses import replace
from importlib.util import find_spec
from typing import Any

from src.assets.asset_coordinator import AssetCoordinator
from src.campaigns.campaign_composer import CampaignComposer
from src.adapters.platform_adapter import PlatformAdapter
from src.cli.cli_config import build_safe_config_summary, parse_csv_list
from src.governance.content_governance import ContentGovernanceEngine
from src.llm.openai_client import OpenAIClient
from src.output.output_contracts import list_supported_output_types, normalize_output_content_type
from src.output.output_formatter import OutputFormatter
from src.output.output_validator import OutputValidator
from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger


SAMPLE_VALIDATE_TEXT = {
    "instagram_post": "Discover a calm Mallorca lifestyle with trusted local guidance. Request a viewing today. #Mallorca #RealEstate",
    "instagram_reel": "A calm Mallorca lifestyle with trusted local guidance. Request a viewing today. #Mallorca #RealEstate",
    "property_description": "Rustic exterior, modern comfort inside, with practical access to services and nearby beaches.",
    "image_prompt": "Mediterranean home with natural light, premium but approachable styling, and a calm Mallorca mood.",
    "video_prompt": "Scene opens on a calm Mediterranean home, with gentle camera motion and a warm lifestyle mood.",
    "campaign_asset": "A calm Mallorca lifestyle with trusted local guidance and a clear call to action.",
}


def handle_generate(args: Any) -> dict[str, Any]:
    """Handle the generate command."""

    logger = get_logger("cli.generate")
    pipeline_config = _build_pipeline_config(args, enable_live_generation=not bool(getattr(args, "dry_run", False)))
    pipeline = ContentGenerationPipeline(config=pipeline_config, logger=logger)
    request = _build_generation_request(args)
    dry_run = bool(getattr(args, "dry_run", False))
    export_requested = bool(getattr(args, "export", False)) and not dry_run

    if dry_run:
        return _run_generate_dry_run(pipeline, request, export_requested)

    pipeline.config = _replace_pipeline_config(pipeline.config, enable_export=export_requested)
    result = pipeline.generate(request)
    return _wrap_command_result(
        command="generate",
        success=bool(result.get("success")),
        mode="live",
        brand=str(result.get("brand", request.get("brand", ""))),
        platform=str(result.get("platform", request.get("platform", ""))),
        content_type=str(result.get("content_type", request.get("content_type", ""))),
        summary=_build_generate_summary(result, request, dry_run=False),
        payload=_strip_sensitive_payload(result),
        warnings=list(result.get("warnings", [])),
        errors=[str(result.get("error"))] if result.get("error") else [],
        metadata={"export_requested": export_requested},
    )


def handle_campaign(args: Any) -> dict[str, Any]:
    """Handle the campaign command."""

    logger = get_logger("cli.campaign")
    composer = CampaignComposer(output_root=PipelineConfig().campaign_output_root, logger=logger)
    request = _build_campaign_request(args)
    dry_run = bool(getattr(args, "dry_run", False))
    if not dry_run and bool(getattr(args, "export", False)):
        request["enable_export"] = True

    result = composer.compose(request, assets={})
    return _wrap_command_result(
        command="campaign",
        success=bool(result.get("success")),
        mode="dry_run" if dry_run else "live",
        brand=str(result.get("brand", request.get("brand", ""))),
        campaign_type=str(result.get("campaign_type", request.get("campaign_type", ""))),
        audience=str(result.get("audience", request.get("audience", ""))),
        location=str(result.get("location", request.get("location", ""))),
        objective=str(result.get("objective", request.get("objective", ""))),
        summary=_build_campaign_summary(result),
        payload=_strip_sensitive_payload(result),
        warnings=list(result.get("warnings", [])),
        errors=list(result.get("errors", [])),
        metadata={"export_requested": bool(getattr(args, "export", False)) and not dry_run},
    )


def handle_assets(args: Any) -> dict[str, Any]:
    """Handle the assets command."""

    logger = get_logger("cli.assets")
    coordinator = AssetCoordinator(output_root=PipelineConfig().asset_output_root, logger=logger)
    request = _build_asset_request(args)
    dry_run = bool(getattr(args, "dry_run", False))
    if not dry_run and bool(getattr(args, "export", False)):
        request["enable_export"] = True

    result = coordinator.coordinate(request)
    return _wrap_command_result(
        command="assets",
        success=bool(result.get("success")),
        mode="dry_run" if dry_run else "live",
        brand=str(result.get("brand", request.get("brand", ""))),
        campaign_type=str(result.get("campaign_type", request.get("campaign_type", ""))),
        audience=str(result.get("audience", request.get("audience", ""))),
        location=str(result.get("location", request.get("location", ""))),
        objective=str(result.get("objective", request.get("objective", ""))),
        summary=_build_asset_summary(result),
        payload=_strip_sensitive_payload(result),
        warnings=list(result.get("warnings", [])),
        errors=list(result.get("errors", [])),
        metadata={"export_requested": bool(getattr(args, "export", False)) and not dry_run},
    )


def handle_validate(args: Any) -> dict[str, Any]:
    """Handle the validate command."""

    logger = get_logger("cli.validate")
    content_type = normalize_output_content_type(str(getattr(args, "content_type", "") or "instagram_post"))
    supported_types = set(list_supported_output_types())
    if content_type not in supported_types:
        error = f"Unsupported content type: {getattr(args, 'content_type', '') or content_type}"
        return _wrap_command_result(
            command="validate",
            success=False,
            mode="inspection",
            content_type=str(getattr(args, "content_type", "") or content_type),
            summary={"status": "rejected", "content_type": content_type},
            payload={},
            warnings=[],
            errors=[error],
        )

    brand = normalize_key(str(getattr(args, "brand", "") or "wenzel_partner"))
    platform = normalize_key(str(getattr(args, "platform", "") or "instagram"))
    text = str(getattr(args, "text", "") or SAMPLE_VALIDATE_TEXT.get(content_type, SAMPLE_VALIDATE_TEXT["campaign_asset"])).strip()

    formatter = OutputFormatter(logger=logger)
    validator = OutputValidator(logger=logger)
    governance = ContentGovernanceEngine(logger=logger)

    parsed_output = {"content": text, "raw_content": text}
    formatted_output = formatter.format(parsed_output, content_type)
    validation_result = validator.validate(formatted_output, content_type)
    governance_payload = {
        "brand": brand,
        "platform": platform,
        "content_type": content_type,
        "formatted_output": formatted_output,
        "platform_variants": {platform: {"content": formatted_output}},
        "metadata": {
            "brand": brand,
            "platform": platform,
            "content_type": content_type,
            "objective": "validation",
            "audience": "general",
        },
    }
    governance_result = governance.evaluate(governance_payload)

    return _wrap_command_result(
        command="validate",
        success=True,
        mode="inspection",
        brand=brand,
        platform=platform,
        content_type=content_type,
        summary={
            "approved": bool(governance_result.get("approved", False)),
            "status": governance_result.get("status", "unknown"),
            "overall_score": governance_result.get("overall_score", 0.0),
            "quality_score": governance_result.get("quality_score", 0.0),
            "brand_score": governance_result.get("brand_score", 0.0),
            "platform_score": governance_result.get("platform_score", 0.0),
            "factual_safety_score": governance_result.get("factual_safety_score", 0.0),
        },
        payload={
            "formatted_output": formatted_output,
            "validation_result": validation_result,
            "governance_result": governance_result,
        },
        warnings=list(validation_result.get("warnings", [])) + list(governance_result.get("warnings", [])),
        errors=list(validation_result.get("errors", [])) + list(governance_result.get("errors", [])),
    )


def handle_smoke(args: Any) -> dict[str, Any]:
    """Handle the smoke command."""

    logger = get_logger("cli.smoke")
    modules = {
        "openai": find_spec("openai") is not None,
        "dotenv": find_spec("dotenv") is not None,
        "src.pipeline": find_spec("src.pipeline") is not None,
        "src.prompts": find_spec("src.prompts") is not None,
        "src.llm": find_spec("src.llm") is not None,
        "src.output": find_spec("src.output") is not None,
        "src.adapters": find_spec("src.adapters") is not None,
        "src.governance": find_spec("src.governance") is not None,
        "src.campaigns": find_spec("src.campaigns") is not None,
        "src.assets": find_spec("src.assets") is not None,
    }
    pipeline = ContentGenerationPipeline(logger=logger)
    openai_client = OpenAIClient(logger=logger)
    safe_config = build_safe_config_summary()

    checks: dict[str, Any] = dict(modules)
    checks["openai_sdk_available"] = modules["openai"]
    checks["openai_api_key_present"] = safe_config["openai_api_key_present"]
    checks["openai_client_initialized"] = openai_client._client is not None

    brands = pipeline.knowledge_loader.detect_brands()
    sample_brand = "wenzel_partner" if "wenzel_partner" in brands else (brands[0] if brands else "")
    if sample_brand:
        sample_request = {
            "brand": sample_brand,
            "platform": "instagram",
            "content_type": "instagram_post",
            "objective": "generate_leads",
            "audience": "relocation_clients",
            "location": "sant_llorenc_des_cardassar",
            "property_type": "rustic_home",
            "extra_notes": "Smoke test request.",
        }
        is_valid, validation_error = pipeline.validate_request(sample_request)
        checks["pipeline_request_valid"] = is_valid
        if not is_valid and validation_error:
            checks["pipeline_request_error"] = validation_error
        context = pipeline.load_context(sample_brand)
        checks["context_loaded"] = bool(context.get("loaded"))
        prompt_result = pipeline.build_prompt(sample_request, context)
        checks["prompt_built"] = bool(prompt_result.get("prompt_payload"))
    else:
        checks["pipeline_request_valid"] = False
        checks["context_loaded"] = False
        checks["prompt_built"] = False

    formatter = OutputFormatter(logger=logger)
    validator = OutputValidator(logger=logger)
    adapter = PlatformAdapter(logger=logger)
    governance = ContentGovernanceEngine(logger=logger)
    composer = CampaignComposer(logger=logger)
    coordinator = AssetCoordinator(logger=logger)

    sample_formatted = formatter.format(
        {
            "json": {
                "hook": "Discover Mallorca with trusted local guidance.",
                "caption": "A calm, premium-but-approachable home search starts here.",
                "cta": "Request a private viewing",
                "hashtags": ["#Mallorca", "#RealEstate"],
            },
            "raw_content": SAMPLE_VALIDATE_TEXT["instagram_post"],
        },
        "instagram_post",
    )
    checks["formatter_ready"] = bool(sample_formatted)
    checks["validator_ready"] = bool(validator.validate(sample_formatted, "instagram_post").get("valid"))
    checks["adapter_ready"] = bool(
        adapter.adapt(
            {
                "content_type": "property_description",
                "formatted_output": {
                    "title": "Rustic home near Sant Llorenc des Cardassar",
                    "short_description": "A calm Mallorca property with modern comfort.",
                    "long_description": "Rustic outside, modern inside, with practical access to services and nearby beaches.",
                    "highlights": ["Quiet setting", "Modern interiors", "Near beaches"],
                    "cta": "Request a viewing",
                    "hashtags": ["#Mallorca", "#RealEstate"],
                },
                "metadata": {"brand": sample_brand or "sample_brand"},
            },
            ["instagram"],
        ).get("success")
    )
    checks["governance_ready"] = bool(governance.evaluate({"brand": sample_brand or "sample_brand", "platform": "instagram", "content_type": "instagram_post", "formatted_output": sample_formatted, "platform_variants": {"instagram": {"content": sample_formatted}}, "metadata": {"objective": "smoke"}}).get("success"))
    checks["campaign_ready"] = bool(composer.validate_campaign_request({
        "brand": sample_brand or "sample_brand",
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
    })[0])
    checks["asset_ready"] = bool(coordinator.validate_asset_request({
        "brand": sample_brand or "sample_brand",
        "campaign_type": "property_launch",
        "objective": "generate_leads",
        "audience": "relocation_clients",
        "location": "sant_llorenc_des_cardassar",
        "assets_required": ["image_prompt", "video_prompt"],
        "platforms": ["instagram", "facebook"],
        "creative_direction": "Smoke test",
    })[0])

    success = all(
        checks[key]
        for key in (
            "openai_sdk_available",
            "src.pipeline",
            "src.prompts",
            "src.llm",
            "src.output",
            "src.adapters",
            "src.governance",
            "src.campaigns",
            "src.assets",
            "pipeline_request_valid",
            "context_loaded",
            "prompt_built",
            "formatter_ready",
            "validator_ready",
            "adapter_ready",
            "governance_ready",
            "campaign_ready",
            "asset_ready",
        )
    )

    return _wrap_command_result(
        command="smoke",
        success=success,
        mode="inspection",
        summary={"checks_passed": sum(1 for value in checks.values() if bool(value)), "checks_total": len(checks)},
        payload={"checks": checks},
        warnings=[],
        errors=[] if success else ["One or more smoke checks failed."],
    )


def handle_config(args: Any) -> dict[str, Any]:
    """Handle the config command."""

    summary = build_safe_config_summary()
    return _wrap_command_result(
        command="config",
        success=True,
        mode="inspection",
        summary=summary,
        payload=summary,
        warnings=[],
        errors=[],
    )


def _build_pipeline_config(args: Any, enable_live_generation: bool) -> PipelineConfig:
    """Build a pipeline config from CLI arguments."""

    return PipelineConfig(
        enable_live_generation=enable_live_generation,
        enable_export=bool(getattr(args, "export", False)) and enable_live_generation,
        enable_campaign_export=bool(getattr(args, "export", False)),
        enable_asset_export=bool(getattr(args, "export", False)),
    )


def _replace_pipeline_config(config: PipelineConfig, **updates: Any) -> PipelineConfig:
    """Return a new pipeline config with requested field overrides."""

    return replace(config, **updates)


def _build_generation_request(args: Any) -> dict[str, Any]:
    """Build a structured generate request from CLI arguments."""

    return {
        "brand": str(getattr(args, "brand", "") or "").strip(),
        "platform": normalize_key(str(getattr(args, "platform", "") or "").strip()),
        "content_type": normalize_key(str(getattr(args, "content_type", "") or "").strip()),
        "objective": str(getattr(args, "objective", "") or "").strip(),
        "audience": str(getattr(args, "audience", "") or "").strip(),
        "location": normalize_key(str(getattr(args, "location", "") or "").strip()),
        "property_type": normalize_key(str(getattr(args, "property_type", "") or "").strip()),
        "extra_notes": str(getattr(args, "extra_notes", "") or "").strip(),
        "export": bool(getattr(args, "export", False)),
    }


def _build_campaign_request(args: Any) -> dict[str, Any]:
    """Build a structured campaign request from CLI arguments."""

    platforms = parse_csv_list(getattr(args, "platforms", None), default=["instagram", "facebook", "linkedin", "email"])
    assets = parse_csv_list(getattr(args, "assets", None))
    return {
        "brand": str(getattr(args, "brand", "") or "").strip(),
        "campaign_type": normalize_key(str(getattr(args, "campaign_type", "") or "").strip()),
        "objective": str(getattr(args, "objective", "") or "generate_leads").strip(),
        "audience": str(getattr(args, "audience", "") or "general").strip(),
        "location": normalize_key(str(getattr(args, "location", "") or "").strip()),
        "property_type": normalize_key(str(getattr(args, "property_type", "") or "").strip()),
        "platforms": platforms,
        "assets_required": assets,
        "extra_notes": str(getattr(args, "extra_notes", "") or "").strip(),
        "enable_export": bool(getattr(args, "export", False)) and not bool(getattr(args, "dry_run", False)),
    }


def _build_asset_request(args: Any) -> dict[str, Any]:
    """Build a structured asset coordination request from CLI arguments."""

    platforms = parse_csv_list(getattr(args, "platforms", None), default=["instagram", "facebook", "linkedin"])
    assets = parse_csv_list(getattr(args, "assets", None))
    return {
        "brand": str(getattr(args, "brand", "") or "").strip(),
        "campaign_type": normalize_key(str(getattr(args, "campaign_type", "") or "").strip()),
        "objective": str(getattr(args, "objective", "") or "generate_leads").strip(),
        "audience": str(getattr(args, "audience", "") or "general").strip(),
        "location": normalize_key(str(getattr(args, "location", "") or "").strip()),
        "property_type": normalize_key(str(getattr(args, "property_type", "") or "").strip()),
        "platforms": platforms,
        "assets_required": assets,
        "creative_direction": str(getattr(args, "creative_direction", "") or "").strip(),
        "visual_style": str(getattr(args, "visual_style", "") or "").strip(),
        "extra_notes": str(getattr(args, "extra_notes", "") or "").strip(),
        "enable_export": bool(getattr(args, "export", False)) and not bool(getattr(args, "dry_run", False)),
    }


def _run_generate_dry_run(pipeline: ContentGenerationPipeline, request: dict[str, Any], export_requested: bool) -> dict[str, Any]:
    """Execute a generate dry-run without calling external APIs."""

    valid, validation_error = pipeline.validate_request(request)
    if not valid:
        return _wrap_command_result(
            command="generate",
            success=False,
            mode="dry_run",
            dry_run=True,
            brand=request.get("brand", ""),
            platform=request.get("platform", ""),
            content_type=request.get("content_type", ""),
            summary={"status": "validation_failed"},
            payload={},
            warnings=[],
            errors=[validation_error or "Invalid request."],
            metadata={"export_requested": export_requested},
        )

    context = pipeline.load_context(request["brand"])
    if not context.get("loaded"):
        return _wrap_command_result(
            command="generate",
            success=False,
            mode="dry_run",
            dry_run=True,
            brand=request.get("brand", ""),
            platform=request.get("platform", ""),
            content_type=request.get("content_type", ""),
            summary={"status": "context_missing"},
            payload={"context_summary": context.get("summary", {})},
            warnings=list(context.get("warnings", [])),
            errors=[str(context.get("error") or "Brand context is missing.")],
            metadata={"export_requested": export_requested},
        )

    prompt_result = pipeline.build_prompt(request, context)
    if prompt_result.get("errors"):
        return _wrap_command_result(
            command="generate",
            success=False,
            mode="dry_run",
            dry_run=True,
            brand=request.get("brand", ""),
            platform=request.get("platform", ""),
            content_type=request.get("content_type", ""),
            summary={"status": "prompt_build_failed"},
            payload={"context_summary": context.get("summary", {}), "prompt_result": prompt_result},
            warnings=list(prompt_result.get("errors", [])),
            errors=list(prompt_result.get("errors", [])),
            metadata={"export_requested": export_requested},
        )

    prompt_payload = prompt_result.get("prompt_payload", {})
    route = pipeline.router.route(
        content_type=str(request.get("content_type", "")),
        provider=str(pipeline.config.default_generation_setting("provider", "openai")),
        preferred_model=str(pipeline.config.default_generation_setting("model", "")),
        platform=str(request.get("platform", "")),
    )
    return _wrap_command_result(
        command="generate",
        success=True,
        mode="dry_run",
        dry_run=True,
        brand=request.get("brand", ""),
        platform=request.get("platform", ""),
        content_type=request.get("content_type", ""),
        summary=_build_generate_summary({"metadata": {"routing": route.to_dict()}, "prompt_payload": prompt_payload}, request, dry_run=True),
        payload={
            "context_summary": context.get("summary", {}),
            "prompt_payload": prompt_payload,
            "planned_route": route.to_dict(),
            "planned_execution": [
                "validate request",
                "load brand context",
                "build prompt payload",
                "route model",
                "skip OpenAI generation in dry-run",
                "skip export in dry-run" if export_requested else "no export requested",
            ],
        },
        warnings=list(context.get("warnings", [])) + list(prompt_result.get("errors", [])),
        errors=[],
        metadata={"export_requested": export_requested},
    )


def _build_generate_summary(result: dict[str, Any], request: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    """Build a generate command summary."""

    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    routing = metadata.get("routing") if isinstance(metadata.get("routing"), dict) else {}
    prompt_payload = result.get("prompt_payload") if isinstance(result.get("prompt_payload"), dict) else {}
    summary = {
        "mode": "dry_run" if dry_run else "live",
        "objective": request.get("objective", ""),
        "audience": request.get("audience", ""),
        "location": request.get("location", ""),
        "prompt_summary": prompt_payload.get("prompt_summary") if prompt_payload else "",
        "route": routing.get("route_reason") or routing.get("model_name") or routing.get("model") or "",
        "exported": bool(result.get("exported_files")),
        "export_paths": result.get("exported_files", {}),
    }
    if not dry_run and isinstance(result.get("validation_result"), dict):
        summary["validation_status"] = result.get("validation_result", {}).get("valid")
    return summary


def _build_campaign_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Build a campaign command summary."""

    return {
        "campaign_name": result.get("campaign_name", ""),
        "campaign_type": result.get("campaign_type", ""),
        "strategy": result.get("strategy", {}),
        "platform_plan": result.get("platform_plan", {}),
        "content_sequence": result.get("content_sequence", []),
        "governance_summary": result.get("governance_summary", {}),
        "export_paths": result.get("export_paths", {}),
    }


def _build_asset_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Build an asset command summary."""

    return {
        "campaign_type": result.get("campaign_type", ""),
        "asset_plan": result.get("asset_plan", {}),
        "asset_requirements": result.get("asset_requirements", {}),
        "missing_assets": result.get("missing_assets", []),
        "validation_result": result.get("validation_result", {}),
        "governance_summary": result.get("assets", {}).get("governance_summary", {}) if isinstance(result.get("assets"), dict) else {},
        "export_paths": result.get("export_paths", {}),
    }


def _wrap_command_result(
    *,
    command: str,
    success: bool,
    mode: str,
    summary: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    brand: str = "",
    platform: str = "",
    content_type: str = "",
    campaign_type: str = "",
    audience: str = "",
    location: str = "",
    objective: str = "",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Wrap a command response in a stable CLI envelope."""

    return {
        "command": command,
        "success": success,
        "mode": mode,
        "dry_run": dry_run,
        "brand": brand,
        "platform": platform,
        "content_type": content_type,
        "campaign_type": campaign_type,
        "audience": audience,
        "location": location,
        "objective": objective,
        "summary": summary or {},
        "payload": payload or {},
        "warnings": warnings or [],
        "errors": errors or [],
        "metadata": metadata or {},
    }


def _strip_sensitive_payload(payload: Any) -> Any:
    """Remove provider raw responses from payloads before display."""

    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if str(key).lower() == "raw_response":
                continue
            sanitized[key] = _strip_sensitive_payload(value)
        return sanitized
    if isinstance(payload, list):
        return [_strip_sensitive_payload(item) for item in payload]
    return payload
