"""End-to-end AI content generation pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Any
import json

from src.core.context_builder import ContextBuilder
from src.core.knowledge_loader import BrandKnowledge, KnowledgeLoader
from src.llm.llm_router import LLMRouter
from src.llm.openai_client import OpenAIClient
from src.llm.response_parser import ResponseParser
from src.output.output_exporter import OutputExporter
from src.output.output_formatter import OutputFormatter
from src.output.output_metadata import build_output_metadata
from src.output.output_renderer import OutputRenderer
from src.output.output_validator import OutputValidator
from src.reporting.reporting_engine import ReportingEngine
from src.creative.creative_direction_engine import CreativeDirectionEngine
from src.creative.creative_validator import CreativeDirectionValidator
from src.adapters.platform_adapter import PlatformAdapter
from src.assets.asset_coordinator import AssetCoordinator
from src.assets.asset_contracts import normalize_asset_type
from src.governance.content_governance import ContentGovernanceEngine
from src.campaigns.campaign_composer import CampaignComposer
from src.campaigns.campaign_contracts import get_campaign_contract
from src.media.image_prompt_engine import ImagePromptEngine
from src.media.image_prompt_validator import ImagePromptValidator
from src.media.video_script_engine import VideoScriptEngine
from src.media.video_script_validator import VideoScriptValidator
from src.pipeline.pipeline_config import PipelineConfig
from src.pipeline.pipeline_result import build_failure_result, build_success_result
from src.tracking.token_tracker import TokenTracker
from src.prompts.prompt_builder import PromptBuilder
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context, log_error, log_scan, log_warning


class ContentGenerationPipeline:
    """Coordinate context loading, prompt assembly, model generation, and parsing."""

    def __init__(
        self,
        config: PipelineConfig | None = None,
        logger: Any | None = None,
        knowledge_loader: KnowledgeLoader | None = None,
        context_builder: ContextBuilder | None = None,
        prompt_builder: PromptBuilder | None = None,
        router: LLMRouter | None = None,
        client: OpenAIClient | None = None,
        parser: ResponseParser | None = None,
        formatter: OutputFormatter | None = None,
        validator: OutputValidator | None = None,
        renderer: OutputRenderer | None = None,
        exporter: OutputExporter | None = None,
        adapter: PlatformAdapter | None = None,
        governance_engine: ContentGovernanceEngine | None = None,
        campaign_composer: CampaignComposer | None = None,
        asset_coordinator: AssetCoordinator | None = None,
        reporting_engine: ReportingEngine | None = None,
        image_prompt_engine: ImagePromptEngine | None = None,
        image_prompt_validator: ImagePromptValidator | None = None,
        video_script_engine: VideoScriptEngine | None = None,
        video_script_validator: VideoScriptValidator | None = None,
        creative_direction_engine: CreativeDirectionEngine | None = None,
        creative_direction_validator: CreativeDirectionValidator | None = None,
    ) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.config = config or PipelineConfig()
        self.knowledge_loader = knowledge_loader or KnowledgeLoader(brands_root=self.config.brands_root, logger=self.logger)
        self.context_builder = context_builder or ContextBuilder(logger=self.logger)
        self.prompt_builder = prompt_builder or PromptBuilder(brands_root=self.config.brands_root, logger=self.logger)
        self.router = router or LLMRouter(logger=self.logger)
        self.client = client or OpenAIClient(logger=self.logger)
        self.parser = parser or ResponseParser(logger=self.logger)
        self.formatter = formatter or OutputFormatter(logger=self.logger)
        self.validator = validator or OutputValidator(logger=self.logger)
        self.renderer = renderer or OutputRenderer(logger=self.logger)
        self.exporter = exporter or OutputExporter(output_root=self.config.output_root, logger=self.logger)
        self.adapter = adapter or PlatformAdapter(logger=self.logger)
        self.governance_engine = governance_engine or ContentGovernanceEngine(logger=self.logger)
        self.campaign_composer = campaign_composer or CampaignComposer(output_root=self.config.campaign_output_root, logger=self.logger)
        self.asset_coordinator = asset_coordinator or AssetCoordinator(output_root=self.config.asset_output_root, logger=self.logger)
        self.reporting_engine = reporting_engine or ReportingEngine(output_root=self.config.report_output_root, logger=self.logger)
        self.token_tracker = TokenTracker(logger=self.logger)
        self.image_prompt_engine = image_prompt_engine or ImagePromptEngine(logger=self.logger)
        self.image_prompt_validator = image_prompt_validator or ImagePromptValidator()
        self.video_script_engine = video_script_engine or VideoScriptEngine(logger=self.logger)
        self.video_script_validator = video_script_validator or VideoScriptValidator()
        self.creative_direction_engine = creative_direction_engine or CreativeDirectionEngine(logger=self.logger)
        self.creative_direction_validator = creative_direction_validator or CreativeDirectionValidator()

    def generate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Generate content from a structured request."""

        return self._generate(request)

    def validate_request(self, request: dict[str, Any]) -> tuple[bool, str | None]:
        """Validate a generation request."""

        if not isinstance(request, dict):
            return False, "Request must be a dictionary."

        required_fields = self.config.validation_rules.get("required_fields", ())
        for field_name in required_fields:
            if not str(request.get(field_name, "")).strip():
                return False, f"Missing required field: {field_name}"

        brand = normalize_key(str(request.get("brand", "")))
        platform = normalize_key(str(request.get("platform", "")))
        content_type = normalize_key(str(request.get("content_type", "")))
        if not brand:
            return False, "Missing brand."
        if not self.config.supports_platform(platform):
            return False, f"Unsupported platform: {platform}"
        if not self.config.supports_content_type(content_type):
            return False, f"Unsupported content type: {content_type}"
        return True, None

    def load_context(self, brand: str) -> dict[str, Any]:
        """Load brand context and build a reusable summary."""

        normalized_brand = normalize_key(brand)
        log_scan(self.logger, f"Loading brand context for {normalized_brand}")
        bundle = self.knowledge_loader.load_brand(normalized_brand)
        if not (bundle.brand_config or bundle.knowledge_base):
            return self._empty_context_summary(normalized_brand, bundle, "Brand context not found.")

        context = self.context_builder.build_brand_context(bundle)
        summary = self.context_builder.build_summarized_context(bundle)
        combined_context = self.context_builder.build_combined_context(bundle)
        storytelling_context = self.context_builder.build_storytelling_context(bundle)
        log_context(self.logger, f"Context loaded for {normalized_brand}")
        return {
            "brand": normalized_brand,
            "brand_root": bundle.brand_root,
            "bundle": bundle,
            "context": context,
            "summary": summary,
            "combined_context": combined_context,
            "storytelling_context": storytelling_context,
            "detected_categories": bundle.detected_categories,
            "warnings": bundle.warnings,
            "loaded": True,
            "error": None,
        }

    def build_prompt(self, request: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Build a prompt payload using the existing prompt orchestration layer."""

        if not context.get("loaded"):
            return {"errors": [context.get("error") or "Context is not loaded."], "prompt_payload": None}

        request_payload = self._normalize_request(request)
        request_payload["extra_context"] = self._build_extra_context(context, request_payload)
        log_context(self.logger, f"Building prompt for {request_payload['brand']}/{request_payload['platform']}/{request_payload['content_type']}")
        prompt_payload = self.prompt_builder.build_prompt(request_payload)
        if prompt_payload.get("errors"):
            return {"errors": prompt_payload["errors"], "prompt_payload": None}
        return {"errors": [], "prompt_payload": prompt_payload}

    def generate_ai_response(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        """Send the prompt payload to OpenAI through the integration layer."""

        log_context(self.logger, f"Routing generation for {prompt_payload.get('brand', '')}/{prompt_payload.get('content_type', '')}")
        return self.client.generate_text(prompt_payload)

    def parse_response(self, ai_response: dict[str, Any]) -> dict[str, Any]:
        """Normalize the AI response using the response parser."""

        log_context(self.logger, "Parsing AI response")
        return self.parser.parse_text_response(ai_response)

    def build_result(
        self,
        success: bool,
        request: dict[str, Any],
        context: dict[str, Any],
        prompt_payload: dict[str, Any] | None,
        ai_response: dict[str, Any] | None,
        parsed_output: dict[str, Any] | None,
        formatted_output: dict[str, Any] | None,
        validation_result: dict[str, Any] | None,
        adaptation_result: dict[str, Any] | None,
        platform_variants: dict[str, Any] | None,
        governance_result: dict[str, Any] | None = None,
        approval_status: str = "unknown",
        overall_quality_score: float | None = None,
        governance_warnings: list[str] | None = None,
        governance_errors: list[str] | None = None,
        campaign_result: dict[str, Any] | None = None,
        campaign_strategy: dict[str, Any] | None = None,
        campaign_assets: dict[str, Any] | None = None,
        campaign_governance_summary: dict[str, Any] | None = None,
        campaign_export_paths: dict[str, str] | None = None,
        asset_coordination_result: dict[str, Any] | None = None,
        asset_plan: dict[str, Any] | None = None,
        asset_requirements: dict[str, Any] | None = None,
        missing_assets: list[str] | None = None,
        asset_export_paths: dict[str, str] | None = None,
        execution_report: dict[str, Any] | None = None,
        governance_report: dict[str, Any] | None = None,
        campaign_report: dict[str, Any] | None = None,
        asset_report: dict[str, Any] | None = None,
        export_report: dict[str, Any] | None = None,
        consolidated_report: dict[str, Any] | None = None,
        report_export_paths: dict[str, str] | None = None,
        rendered_markdown: str | None = None,
        rendered_text: str | None = None,
        exported_files: dict[str, str] | None = None,
        output_metadata: dict[str, Any] | None = None,
        token_usage: dict[str, Any] | None = None,
        execution_token_summary: dict[str, Any] | None = None,
        module_token_summary: dict[str, Any] | None = None,
        provider_token_summary: dict[str, Any] | None = None,
        estimated_token_usage: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        error: str | None = None,
        warnings: list[str] | None = None,
        image_prompt_result: dict[str, Any] | None = None,
        enhanced_image_prompt: str | None = None,
        negative_prompt: str | None = None,
        visual_style: str | None = None,
        cinematic_rules_applied: list[str] | None = None,
        image_prompt_validation: dict[str, Any] | None = None,
        video_script_result: dict[str, Any] | None = None,
        video_type: str | None = None,
        video_duration: str | None = None,
        scene_sequence: list[dict[str, Any]] | None = None,
        storyboard: list[dict[str, Any]] | None = None,
        voiceover: str | None = None,
        camera_direction: dict[str, Any] | None = None,
        music_mood: str | None = None,
        video_script_validation: dict[str, Any] | None = None,
        creative_direction_result: dict[str, Any] | None = None,
        creative_direction_type: str | None = None,
        visual_identity: dict[str, Any] | None = None,
        moodboard: dict[str, Any] | None = None,
        color_palette: dict[str, Any] | None = None,
        platform_creative_guidelines: dict[str, Any] | None = None,
        media_guidelines: dict[str, Any] | None = None,
        creative_validation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a structured pipeline result."""

        normalized_request = self._normalize_request(request)
        metadata_payload = metadata or {}
        token_usage = token_usage if token_usage is not None else metadata_payload.get("token_usage")
        execution_token_summary = execution_token_summary if execution_token_summary is not None else metadata_payload.get("execution_token_summary")
        module_token_summary = module_token_summary if module_token_summary is not None else metadata_payload.get("module_token_summary")
        provider_token_summary = provider_token_summary if provider_token_summary is not None else metadata_payload.get("provider_token_summary")
        estimated_token_usage = estimated_token_usage if estimated_token_usage is not None else metadata_payload.get("estimated_token_usage")
        if success:
            result = build_success_result(
                brand=normalized_request["brand"],
                platform=normalized_request["platform"],
                content_type=normalized_request["content_type"],
                input_request=normalized_request,
                context_summary=context.get("summary", {}),
                prompt_payload=prompt_payload or {},
                ai_response=ai_response or {},
                parsed_output=parsed_output or {},
                formatted_output=formatted_output,
                validation_result=validation_result,
                image_prompt_result=image_prompt_result,
                enhanced_image_prompt=enhanced_image_prompt,
                negative_prompt=negative_prompt,
                visual_style=visual_style,
                cinematic_rules_applied=cinematic_rules_applied,
                image_prompt_validation=image_prompt_validation,
                video_script_result=video_script_result,
                video_type=video_type,
                video_duration=video_duration,
                scene_sequence=scene_sequence,
                storyboard=storyboard,
                voiceover=voiceover,
                camera_direction=camera_direction,
                music_mood=music_mood,
                video_script_validation=video_script_validation,
                creative_direction_result=creative_direction_result,
                creative_direction_type=creative_direction_type,
                visual_identity=visual_identity,
                moodboard=moodboard,
                color_palette=color_palette,
                platform_creative_guidelines=platform_creative_guidelines,
                media_guidelines=media_guidelines,
                creative_validation=creative_validation,
                adaptation_result=adaptation_result,
                platform_variants=platform_variants or {},
                governance_result=governance_result,
                approval_status=approval_status,
                overall_quality_score=overall_quality_score,
                governance_warnings=governance_warnings or [],
                governance_errors=governance_errors or [],
                campaign_result=campaign_result,
                campaign_strategy=campaign_strategy,
                campaign_assets=campaign_assets or {},
                campaign_governance_summary=campaign_governance_summary,
                campaign_export_paths=campaign_export_paths or {},
                asset_coordination_result=asset_coordination_result,
                asset_plan=asset_plan or {},
                asset_requirements=asset_requirements or {},
                missing_assets=missing_assets or [],
                asset_export_paths=asset_export_paths or {},
                execution_report=execution_report,
                governance_report=governance_report,
                campaign_report=campaign_report,
                asset_report=asset_report,
                export_report=export_report,
                consolidated_report=consolidated_report,
                report_export_paths=report_export_paths or {},
                rendered_markdown=rendered_markdown,
                rendered_text=rendered_text,
                exported_files=exported_files or {},
                output_metadata=output_metadata or {},
                token_usage=token_usage,
                execution_token_summary=execution_token_summary,
                module_token_summary=module_token_summary,
                provider_token_summary=provider_token_summary,
                estimated_token_usage=estimated_token_usage,
                metadata=metadata,
                warnings=warnings or [],
            )
        else:
            result = build_failure_result(
                brand=normalized_request["brand"],
                platform=normalized_request["platform"],
                content_type=normalized_request["content_type"],
                input_request=normalized_request,
                context_summary=context.get("summary", {}),
                metadata=metadata,
                error=error or "Pipeline failed.",
                prompt_payload=prompt_payload,
                ai_response=ai_response,
                parsed_output=parsed_output,
                formatted_output=formatted_output,
                validation_result=validation_result,
                image_prompt_result=image_prompt_result,
                enhanced_image_prompt=enhanced_image_prompt,
                negative_prompt=negative_prompt,
                visual_style=visual_style,
                cinematic_rules_applied=cinematic_rules_applied,
                image_prompt_validation=image_prompt_validation,
                video_script_result=video_script_result,
                video_type=video_type,
                video_duration=video_duration,
                scene_sequence=scene_sequence,
                storyboard=storyboard,
                voiceover=voiceover,
                camera_direction=camera_direction,
                music_mood=music_mood,
                video_script_validation=video_script_validation,
                creative_direction_result=creative_direction_result,
                creative_direction_type=creative_direction_type,
                visual_identity=visual_identity,
                moodboard=moodboard,
                color_palette=color_palette,
                platform_creative_guidelines=platform_creative_guidelines,
                media_guidelines=media_guidelines,
                creative_validation=creative_validation,
                adaptation_result=adaptation_result,
                platform_variants=platform_variants or {},
                governance_result=governance_result,
                approval_status=approval_status,
                overall_quality_score=overall_quality_score,
                governance_warnings=governance_warnings or [],
                governance_errors=governance_errors or [],
                campaign_result=campaign_result,
                campaign_strategy=campaign_strategy,
                campaign_assets=campaign_assets or {},
                campaign_governance_summary=campaign_governance_summary,
                campaign_export_paths=campaign_export_paths or {},
                asset_coordination_result=asset_coordination_result,
                asset_plan=asset_plan or {},
                asset_requirements=asset_requirements or {},
                missing_assets=missing_assets or [],
                asset_export_paths=asset_export_paths or {},
                execution_report=execution_report,
                governance_report=governance_report,
                campaign_report=campaign_report,
                asset_report=asset_report,
                export_report=export_report,
                consolidated_report=consolidated_report,
                report_export_paths=report_export_paths or {},
                rendered_markdown=rendered_markdown,
                rendered_text=rendered_text,
                exported_files=exported_files or {},
                output_metadata=output_metadata or {},
                token_usage=token_usage,
                execution_token_summary=execution_token_summary,
                module_token_summary=module_token_summary,
                provider_token_summary=provider_token_summary,
                estimated_token_usage=estimated_token_usage,
                warnings=warnings or [],
            )
        return self._attach_reporting(result, request=normalized_request, context=context)

    def _generate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Internal orchestration for a single content generation request."""

        execution_started_at = datetime.now(timezone.utc)
        stage_timings: dict[str, float] = {}

        validation_started = perf_counter()
        is_valid, validation_error = self.validate_request(request)
        stage_timings["validation"] = round(perf_counter() - validation_started, 6)
        normalized_request = self._normalize_request(request)
        base_metadata = self._base_metadata(normalized_request)

        if not is_valid:
            log_warning(self.logger, validation_error or "Request validation failed.")
            base_metadata["execution"] = self._build_execution_metadata(execution_started_at, stage_timings, success=False, stage="validation", error=validation_error or "Request validation failed.")
            return self.build_result(
                success=False,
                request=normalized_request,
                context=self._empty_context_summary(normalized_request["brand"], None, validation_error or "Request validation failed."),
                prompt_payload=None,
                ai_response=None,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                adaptation_result=None,
                platform_variants={},
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=base_metadata,
                error=validation_error or "Request validation failed.",
            )

        context_started = perf_counter()
        context = self.load_context(normalized_request["brand"])
        stage_timings["context_loading"] = round(perf_counter() - context_started, 6)
        if not context.get("loaded"):
            error = context.get("error") or f"Brand context is missing for '{normalized_request['brand']}'."
            log_error(self.logger, error)
            base_metadata["execution"] = self._build_execution_metadata(execution_started_at, stage_timings, success=False, stage="context_loading", error=error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=None,
                ai_response=None,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                adaptation_result=None,
                platform_variants={},
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=base_metadata,
                error=error,
                warnings=context.get("warnings", []),
            )

        creative_direction_result: dict[str, Any] | None = None
        creative_direction_type: str | None = None
        visual_identity: dict[str, Any] | None = None
        moodboard: dict[str, Any] | None = None
        color_palette: dict[str, Any] | None = None
        platform_creative_guidelines: dict[str, Any] | None = None
        media_guidelines: dict[str, Any] | None = None
        creative_validation: dict[str, Any] | None = None

        if self.config.enable_creative_direction_engine or normalized_request["content_type"] == "creative_direction":
            creative_started = perf_counter()
            creative_request = self._build_creative_direction_request(normalized_request, context)
            creative_direction_result = self.creative_direction_engine.generate_creative_direction(creative_request)
            stage_timings["creative_direction"] = round(perf_counter() - creative_started, 6)
            creative_direction_type = str(creative_direction_result.get("creative_direction_type", self.config.default_creative_direction_type))
            if isinstance(creative_direction_result.get("visual_identity"), dict):
                visual_identity = dict(creative_direction_result.get("visual_identity", {}))
            if isinstance(creative_direction_result.get("moodboard"), dict):
                moodboard = dict(creative_direction_result.get("moodboard", {}))
            if isinstance(creative_direction_result.get("color_palette"), dict):
                color_palette = dict(creative_direction_result.get("color_palette", {}))
            if isinstance(creative_direction_result.get("platform_guidelines"), dict):
                platform_creative_guidelines = dict(creative_direction_result.get("platform_guidelines", {}))
            if isinstance(creative_direction_result.get("media_guidelines"), dict):
                media_guidelines = dict(creative_direction_result.get("media_guidelines", {}))
            if isinstance(creative_direction_result.get("validation"), dict):
                creative_validation = dict(creative_direction_result.get("validation", {}))

            if normalized_request["content_type"] == "creative_direction":
                creative_errors = list(creative_direction_result.get("errors", [])) if isinstance(creative_direction_result, dict) else []
                creative_warnings = list(creative_direction_result.get("warnings", [])) if isinstance(creative_direction_result, dict) else []
                creative_metadata = {
                    **base_metadata,
                    "creative_direction_type": creative_direction_type,
                    "visual_identity_used": visual_identity.get("name", "") if isinstance(visual_identity, dict) else "",
                    "moodboard_rule_count": len(moodboard.get("rules", [])) if isinstance(moodboard, dict) else 0,
                    "color_palette_used": color_palette.get("name", "") if isinstance(color_palette, dict) else "",
                }
                creative_metadata["execution"] = self._build_execution_metadata(
                    execution_started_at,
                    stage_timings,
                    success=bool(creative_direction_result.get("success", True)),
                    stage="creative_direction",
                    error="; ".join(creative_errors) if creative_errors else None,
                )
                result = self.build_result(
                    success=bool(creative_direction_result.get("success", True)),
                    request=normalized_request,
                    context=context,
                    prompt_payload=None,
                    ai_response=None,
                    parsed_output=None,
                    formatted_output=None,
                    validation_result=None,
                    adaptation_result=None,
                    platform_variants={},
                    rendered_markdown=None,
                    rendered_text=None,
                    exported_files={},
                    output_metadata=build_output_metadata(
                        brand=normalized_request["brand"],
                        platform=normalized_request["platform"],
                        content_type=normalized_request["content_type"],
                        objective=normalized_request.get("objective", ""),
                        audience=normalized_request.get("audience", ""),
                        location=normalized_request.get("location", ""),
                        property_type=normalized_request.get("property_type", ""),
                        model="",
                        provider="",
                        validation_status="passed" if creative_direction_result.get("success", True) else "failed",
                        export_paths={},
                    ),
                    metadata=creative_metadata,
                    error="; ".join(creative_errors) if creative_errors else None,
                    warnings=creative_warnings,
                    creative_direction_result=creative_direction_result,
                    creative_direction_type=creative_direction_type,
                    visual_identity=visual_identity,
                    moodboard=moodboard,
                    color_palette=color_palette,
                    platform_creative_guidelines=platform_creative_guidelines,
                    media_guidelines=media_guidelines,
                    creative_validation=creative_validation,
                )
                return self._attach_reporting(result, request=normalized_request, context=context)

        prompt_started = perf_counter()
        prompt_result = self.build_prompt(normalized_request, context)
        stage_timings["prompt_building"] = round(perf_counter() - prompt_started, 6)
        if prompt_result.get("errors"):
            error = "; ".join(prompt_result["errors"])
            log_error(self.logger, error)
            base_metadata["execution"] = self._build_execution_metadata(execution_started_at, stage_timings, success=False, stage="prompt_building", error=error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=None,
                ai_response=None,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                adaptation_result=None,
                platform_variants={},
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=base_metadata,
                error=error,
                warnings=prompt_result["errors"],
            )

        prompt_payload = prompt_result["prompt_payload"]
        metadata = self._build_metadata(normalized_request, context, prompt_payload)
        model_route = self.router.route(
            content_type=normalized_request["content_type"],
            provider=str(self.config.default_generation_setting("provider", "openai")),
            preferred_model=str(metadata.get("model") or "") or None,
            platform=normalized_request["platform"],
        )
        metadata.update(
            {
                "provider": model_route.provider,
                "model": model_route.model_name,
                "route_reason": model_route.route_reason,
                "routing": model_route.to_dict(),
            }
        )
        if isinstance(prompt_payload, dict):
            prompt_metadata = prompt_payload.setdefault("metadata", {})
            if isinstance(prompt_metadata, dict):
                prompt_metadata.update(
                    {
                        "provider": model_route.provider,
                        "model": model_route.model_name,
                        "route": model_route.route_reason,
                        "generation_mode": normalized_request["content_type"],
                    }
                )
        log_context(self.logger, f"Model routed to {model_route.provider}/{model_route.model_name}")

        if not self._can_generate_live():
            error = "OpenAI API key missing or live generation disabled; skipping live generation."
            log_warning(self.logger, error)
            metadata["execution"] = self._build_execution_metadata(execution_started_at, stage_timings, success=False, stage="generation", error=error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=prompt_payload,
                ai_response=None,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                adaptation_result=None,
                platform_variants={},
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=metadata,
                error=error,
                warnings=[],
            )

        log_context(self.logger, f"Generating AI output for {normalized_request['brand']}/{normalized_request['content_type']}")
        generation_started = perf_counter()
        ai_response = self.generate_ai_response(prompt_payload)
        stage_timings["generation"] = round(perf_counter() - generation_started, 6)
        if not ai_response.get("success"):
            error = str(ai_response.get("error") or "OpenAI generation failed.")
            log_error(self.logger, error)
            metadata["execution"] = self._build_execution_metadata(execution_started_at, stage_timings, success=False, stage="generation", error=error)
            ai_warnings = list(ai_response.get("metadata", {}).get("warnings", []))
            token_warnings_on_failure = list(ai_response.get("token_usage", {}).get("warnings", [])) if isinstance(ai_response.get("token_usage"), dict) else []
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=prompt_payload,
                ai_response=ai_response,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                adaptation_result=None,
                platform_variants={},
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                token_usage=ai_response.get("token_usage") if isinstance(ai_response.get("token_usage"), dict) else None,
                execution_token_summary=None,
                module_token_summary=None,
                provider_token_summary=None,
                estimated_token_usage=ai_response.get("token_usage") if isinstance(ai_response.get("token_usage"), dict) and ai_response.get("token_usage", {}).get("estimated") else None,
                metadata=metadata,
                error=error,
                warnings=ai_warnings + token_warnings_on_failure,
            )

        token_usage: dict[str, Any] | None = None
        execution_token_summary: dict[str, Any] | None = None
        module_token_summary: dict[str, Any] | None = None
        provider_token_summary: dict[str, Any] | None = None
        estimated_token_usage: dict[str, Any] | None = None
        token_warnings: list[str] = []
        token_errors: list[str] = []
        if self.config.enable_token_tracking:
            token_tracking = self._build_token_tracking(
                request=normalized_request,
                prompt_payload=prompt_payload,
                ai_response=ai_response,
                parsed_output=None,
                metadata=metadata,
                execution_id=execution_started_at.isoformat(),
            )
            token_usage = token_tracking.get("token_usage")
            execution_token_summary = token_tracking.get("execution_token_summary")
            module_token_summary = token_tracking.get("module_token_summary")
            provider_token_summary = token_tracking.get("provider_token_summary")
            estimated_token_usage = token_tracking.get("estimated_token_usage")
            token_warnings = list(token_tracking.get("warnings", []))
            token_errors = list(token_tracking.get("errors", []))
            metadata.update(token_tracking)

        try:
            parsing_started = perf_counter()
            parsed_output = self.parse_response(ai_response)
            stage_timings["parsing"] = round(perf_counter() - parsing_started, 6)
        except Exception as exc:  # pragma: no cover - defensive fallback
            error = f"Response parsing failed: {exc}"
            log_error(self.logger, error)
            metadata["execution"] = self._build_execution_metadata(execution_started_at, stage_timings, success=False, stage="parsing", error=error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=prompt_payload,
                ai_response=ai_response,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                adaptation_result=None,
                platform_variants={},
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=metadata,
                error=error,
                warnings=[],
            )

        if parsed_output.get("parser_warnings"):
            log_warning(self.logger, "; ".join(parsed_output.get("parser_warnings", [])))

        formatted_output = None
        validation_result = None
        adaptation_result = None
        platform_variants: dict[str, Any] = {}
        rendered_markdown = None
        rendered_text = None
        exported_files: dict[str, str] = {}
        output_metadata: dict[str, Any] = {}
        output_errors: list[str] = []
        output_warnings: list[str] = []
        image_prompt_result: dict[str, Any] | None = None
        enhanced_image_prompt: str | None = None
        image_prompt_validation: dict[str, Any] | None = None
        cinematic_rules_applied: list[str] = []
        image_negative_prompt: str | None = None
        image_visual_style: str | None = None
        video_script_result: dict[str, Any] | None = None
        video_type: str | None = None
        video_duration: str | None = None
        scene_sequence: list[dict[str, Any]] = []
        storyboard: list[dict[str, Any]] = []
        voiceover: str | None = None
        camera_direction: dict[str, Any] | None = None
        music_mood: str | None = None
        video_script_validation: dict[str, Any] | None = None
        asset_coordination_result = None
        asset_plan: dict[str, Any] = {}
        asset_requirements: dict[str, Any] = {}
        missing_assets: list[str] = []
        asset_export_paths: dict[str, str] = {}
        execution_report: dict[str, Any] | None = None
        governance_report: dict[str, Any] | None = None
        campaign_report: dict[str, Any] | None = None
        asset_report: dict[str, Any] | None = None
        export_report: dict[str, Any] | None = None
        consolidated_report: dict[str, Any] | None = None
        report_export_paths: dict[str, str] = {}

        if self.config.enable_output_formatting:
            try:
                formatting_started = perf_counter()
                formatted_output = self.formatter.format(parsed_output, normalized_request["content_type"])
                stage_timings["formatting"] = round(perf_counter() - formatting_started, 6)
            except Exception as exc:  # pragma: no cover - defensive fallback
                error = f"Output formatting failed: {exc}"
                log_error(self.logger, error)
                metadata["execution"] = self._build_execution_metadata(execution_started_at, stage_timings, success=False, stage="formatting", error=error)
                return self.build_result(
                    success=False,
                    request=normalized_request,
                    context=context,
                    prompt_payload=prompt_payload,
                    ai_response=ai_response,
                    parsed_output=parsed_output,
                    formatted_output=None,
                    validation_result=None,
                    adaptation_result=None,
                    platform_variants={},
                    rendered_markdown=None,
                    rendered_text=None,
                    exported_files={},
                    output_metadata={},
                    metadata=metadata,
                    error=error,
                    warnings=[],
                )

            if self.config.enable_output_validation:
                validation_result = self.validator.validate(formatted_output, normalized_request["content_type"])
                output_warnings.extend(validation_result.get("warnings", []))
                output_errors.extend(validation_result.get("errors", []))

            if self.config.enable_rendering:
                try:
                    rendering_started = perf_counter()
                    rendered_markdown = self.renderer.render_markdown(formatted_output, normalized_request["content_type"])
                    rendered_text = self.renderer.render_text(formatted_output, normalized_request["content_type"])
                    stage_timings["rendering"] = round(perf_counter() - rendering_started, 6)
                except Exception as exc:  # pragma: no cover - defensive fallback
                    error = f"Output rendering failed: {exc}"
                    log_error(self.logger, error)
                    metadata["execution"] = self._build_execution_metadata(execution_started_at, stage_timings, success=False, stage="rendering", error=error)
                    return self.build_result(
                        success=False,
                        request=normalized_request,
                        context=context,
                        prompt_payload=prompt_payload,
                        ai_response=ai_response,
                        parsed_output=parsed_output,
                        formatted_output=formatted_output,
                        validation_result=validation_result,
                        adaptation_result=None,
                        platform_variants={},
                        rendered_markdown=None,
                        rendered_text=None,
                        exported_files={},
                        output_metadata={},
                        metadata=metadata,
                        error=error,
                        warnings=output_warnings,
                    )

            if self.config.enable_image_prompt_engine and normalized_request["content_type"] == "image_prompt":
                try:
                    image_prompt_started = perf_counter()
                    image_prompt_payload = self._build_image_prompt_request(
                        normalized_request,
                        context,
                        parsed_output,
                        formatted_output,
                        creative_direction_result,
                    )
                    image_prompt_result = self.image_prompt_engine.generate_image_prompt(image_prompt_payload)
                    enhanced_image_prompt = image_prompt_result.get("prompt", "")
                    image_negative_prompt = image_prompt_result.get("negative_prompt", "")
                    image_visual_style = image_prompt_result.get("visual_style", "")
                    cinematic_rules_applied = list(image_prompt_result.get("cinematic_rules_applied", []))
                    image_prompt_validation = image_prompt_result.get("validation", {})
                    stage_timings["image_prompt"] = round(perf_counter() - image_prompt_started, 6)
                except Exception as exc:  # pragma: no cover - defensive fallback
                    warning = f"Image prompt engine failed: {exc}"
                    log_warning(self.logger, warning)
                    image_prompt_result = {
                        "success": False,
                        "warnings": [warning],
                        "errors": [warning],
                    }
                    image_prompt_validation = {
                        "valid": False,
                        "warnings": [warning],
                        "errors": [warning],
                        "scores": {"realism": 0.0, "completeness": 0.0, "brand_fit": 0.0, "platform_fit": 0.0, "conciseness": 0.0},
                    }
                    output_warnings.append(warning)

        if (
            self.config.enable_image_prompt_engine
            and normalized_request["content_type"] == "image_prompt"
            and image_prompt_result is None
        ):
            try:
                image_prompt_started = perf_counter()
                image_prompt_payload = self._build_image_prompt_request(
                    normalized_request,
                    context,
                    parsed_output,
                    formatted_output,
                    creative_direction_result,
                )
                image_prompt_result = self.image_prompt_engine.generate_image_prompt(image_prompt_payload)
                enhanced_image_prompt = image_prompt_result.get("prompt", "")
                image_negative_prompt = image_prompt_result.get("negative_prompt", "")
                image_visual_style = image_prompt_result.get("visual_style", "")
                cinematic_rules_applied = list(image_prompt_result.get("cinematic_rules_applied", []))
                image_prompt_validation = image_prompt_result.get("validation", {})
                stage_timings["image_prompt"] = round(perf_counter() - image_prompt_started, 6)
            except Exception as exc:  # pragma: no cover - defensive fallback
                warning = f"Image prompt engine failed: {exc}"
                log_warning(self.logger, warning)
                image_prompt_result = {
                    "success": False,
                    "warnings": [warning],
                    "errors": [warning],
                }
                image_prompt_validation = {
                    "valid": False,
                    "warnings": [warning],
                    "errors": [warning],
                    "scores": {"realism": 0.0, "completeness": 0.0, "brand_fit": 0.0, "platform_fit": 0.0, "conciseness": 0.0},
                }
                output_warnings.append(warning)

        if self.config.enable_video_script_engine and normalized_request["content_type"] in {"video_script", "video_prompt"}:
            try:
                video_script_started = perf_counter()
                video_script_payload = self._build_video_script_request(
                    normalized_request,
                    context,
                    parsed_output,
                    formatted_output,
                    creative_direction_result,
                )
                video_script_result = self.video_script_engine.generate_video_script(video_script_payload)
                video_type = str(video_script_result.get("video_type", normalized_request.get("video_type", "")))
                video_duration = str(video_script_result.get("duration", normalized_request.get("duration", "")))
                scene_sequence = list(video_script_result.get("scene_sequence", [])) if isinstance(video_script_result.get("scene_sequence"), list) else []
                storyboard = list(video_script_result.get("storyboard", [])) if isinstance(video_script_result.get("storyboard"), list) else []
                voiceover = str(video_script_result.get("voiceover", ""))
                camera_direction = video_script_result.get("camera_direction", {})
                if not isinstance(camera_direction, dict):
                    camera_direction = {"value": camera_direction}
                music_mood = str(video_script_result.get("music_mood", ""))
                video_script_validation = video_script_result.get("validation", {})
                stage_timings["video_script"] = round(perf_counter() - video_script_started, 6)
            except Exception as exc:  # pragma: no cover - defensive fallback
                warning = f"Video script engine failed: {exc}"
                log_warning(self.logger, warning)
                video_script_result = {
                    "success": False,
                    "warnings": [warning],
                    "errors": [warning],
                }
                video_script_validation = {
                    "valid": False,
                    "warnings": [warning],
                    "errors": [warning],
                    "scores": {"structure": 0.0, "pacing": 0.0, "brand_fit": 0.0, "platform_fit": 0.0, "factual_safety": 0.0},
                }
                output_warnings.append(warning)

        validation_status = "passed"
        if validation_result and not validation_result.get("valid", True):
            validation_status = "failed"
        elif validation_result and validation_result.get("warnings"):
            validation_status = "warning"

        if self.config.enable_platform_adaptation and formatted_output:
            target_platforms = list(self.config.target_platforms or self.config.default_target_platforms)
            log_context(self.logger, f"Adapting content for platforms: {target_platforms}")
            try:
                adaptation_started = perf_counter()
                adaptation_request = {
                    "content_type": normalized_request["content_type"],
                    "formatted_output": formatted_output,
                    "metadata": metadata,
                }
                adaptation_result = self.adapter.adapt(adaptation_request, target_platforms)
                platform_variants = dict(adaptation_result.get("platform_variants") or {})
                stage_timings["adaptation"] = round(perf_counter() - adaptation_started, 6)
            except Exception as exc:  # pragma: no cover - defensive fallback
                warning = f"Platform adaptation failed: {exc}"
                log_warning(self.logger, warning)
                adaptation_result = {
                    "success": False,
                    "source_content_type": normalized_request["content_type"],
                    "platform_variants": {},
                    "warnings": [warning],
                    "metadata": metadata,
                    "errors": [warning],
                }
                platform_variants = {}

        governance_result = None
        approval_status = "not_evaluated"
        overall_quality_score = None
        governance_warnings: list[str] = []
        governance_errors: list[str] = []
        if self.config.enable_governance_validation and formatted_output:
            log_context(self.logger, "Evaluating governance")
            governance_payload = {
                "brand": normalized_request["brand"],
                "platform": normalized_request["platform"],
                "content_type": normalized_request["content_type"],
                "formatted_output": formatted_output,
                "platform_variants": platform_variants or {},
                "image_prompt_result": image_prompt_result or {},
                "image_prompt_validation": image_prompt_validation or {},
                "metadata": {
                    "audience": normalized_request.get("audience", ""),
                    "location": normalized_request.get("location", ""),
                    "objective": normalized_request.get("objective", ""),
                },
            }
            governance_started = perf_counter()
            governance_result = self.governance_engine.evaluate(governance_payload)
            stage_timings["governance"] = round(perf_counter() - governance_started, 6)
            approval_status = str(governance_result.get("status", "needs_review"))
            overall_quality_score = float(governance_result.get("overall_score", 0.0))
            governance_warnings = list(governance_result.get("warnings", []))
            governance_errors = list(governance_result.get("errors", []))

            if self.config.reject_on_critical_safety_error and any("critical safety" in err.lower() or "guaranteed" in err.lower() or "risk-free" in err.lower() or "fake exclusivity" in err.lower() or "fake scarcity" in err.lower() or "fake urgency" in err.lower() for err in governance_errors):
                approval_status = "rejected"

            if self.config.enable_export and approval_status in {"approved", "approved_with_warnings"}:
                try:
                    export_started = perf_counter()
                    exported_files = self.exporter.export(
                        brand=normalized_request["brand"],
                        content_type=normalized_request["content_type"],
                        output=formatted_output,
                        metadata=metadata,
                        validation_result=validation_result or {"valid": True, "warnings": [], "errors": []},
                        formats=list(self.config.export_formats),
                    )
                    stage_timings["export"] = round(perf_counter() - export_started, 6)
                except Exception as exc:  # pragma: no cover - defensive fallback
                    log_warning(self.logger, f"Export failed: {exc}")
                    exported_files = {}
        else:
            approval_status = "not_evaluated" if not self.config.enable_governance_validation else "unknown"

            if self.config.enable_export and not self.config.enable_governance_validation:
                try:
                    export_started = perf_counter()
                    exported_files = self.exporter.export(
                        brand=normalized_request["brand"],
                        content_type=normalized_request["content_type"],
                        output=formatted_output,
                        metadata=metadata,
                        validation_result=validation_result or {"valid": True, "warnings": [], "errors": []},
                        formats=list(self.config.export_formats),
                    )
                    stage_timings["export"] = round(perf_counter() - export_started, 6)
                except Exception as exc:  # pragma: no cover - defensive fallback
                    log_warning(self.logger, f"Export failed: {exc}")
                    exported_files = {}

        campaign_result = None
        campaign_strategy = None
        campaign_assets: dict[str, Any] = {}
        campaign_governance_summary = None
        campaign_export_paths: dict[str, str] = {}
        if self.config.enable_campaign_composition:
            log_context(self.logger, "Composing campaign pack")
            campaign_started = perf_counter()
            campaign_type = normalize_key(str(request.get("campaign_type") or self.config.default_campaign_type))
            campaign_contract = get_campaign_contract(campaign_type)
            campaign_request = {
                "brand": normalized_request["brand"],
                "campaign_type": campaign_type,
                "objective": normalized_request.get("objective", ""),
                "audience": normalized_request.get("audience", ""),
                "location": normalized_request.get("location", ""),
                "property_type": normalized_request.get("property_type", ""),
                "platforms": list(campaign_contract.platform_plan.keys()) or list(self.config.default_target_platforms),
                "assets_required": list(campaign_contract.required_assets),
                "extra_notes": normalized_request.get("extra_notes", ""),
                "creative_direction_result": creative_direction_result or {},
                "enable_export": self.config.enable_campaign_export,
            }
            seed_assets = self._build_campaign_assets(
                normalized_request,
                formatted_output,
                platform_variants,
                governance_result,
                image_prompt_result=image_prompt_result,
                video_script_result=video_script_result,
            )
            request_assets = request.get("campaign_assets") if isinstance(request.get("campaign_assets"), dict) else request.get("assets") if isinstance(request.get("assets"), dict) else {}
            if isinstance(request_assets, dict):
                seed_assets.update(request_assets)
            campaign_result = self.campaign_composer.compose(campaign_request, assets=seed_assets)
            stage_timings["campaign_composition"] = round(perf_counter() - campaign_started, 6)
            campaign_strategy = campaign_result.get("strategy")
            campaign_assets = dict(campaign_result.get("assets") or seed_assets)
            campaign_governance_summary = campaign_result.get("governance_summary")
            campaign_export_paths = dict(campaign_result.get("export_paths") or {})

        if self.config.enable_asset_coordination:
            log_context(self.logger, "Coordinating asset plan")
            asset_started = perf_counter()
            campaign_type = normalize_key(str((campaign_result or {}).get("campaign_type") or normalized_request.get("content_type") or self.config.default_campaign_type))
            asset_request = {
                "brand": normalized_request["brand"],
                "campaign_type": campaign_type,
                "objective": normalized_request.get("objective", ""),
                "audience": normalized_request.get("audience", ""),
                "location": normalized_request.get("location", ""),
                "property_type": normalized_request.get("property_type", ""),
                "platforms": list((campaign_result or {}).get("platform_plan", {}).keys()) or list(self.config.default_target_platforms),
                "assets_required": list((campaign_result or {}).get("asset_plan", {}).get("required_assets", [])) or list(normalized_request.get("assets_required", [])) or list(self.config.default_asset_types),
                "creative_direction": normalized_request.get("extra_notes", ""),
                "visual_style": image_visual_style or normalized_request.get("visual_style", ""),
                "image_type": normalized_request.get("image_type", ""),
                "aspect_ratio": normalized_request.get("aspect_ratio", ""),
                "extra_notes": normalized_request.get("extra_notes", ""),
                "creative_direction_result": creative_direction_result or {},
                "campaign_result": campaign_result or {},
                "campaign_strategy": campaign_strategy or {},
                "campaign_assets": campaign_assets or {},
                "image_prompt_result": image_prompt_result or {},
                "video_script_result": video_script_result or {},
                "campaign_metadata": {
                    "campaign_governance_summary": campaign_governance_summary or {},
                    "campaign_export_paths": campaign_export_paths or {},
                },
                "enable_export": self.config.enable_asset_export,
            }
            seed_assets = self._build_asset_seed(
                normalized_request,
                formatted_output,
                platform_variants,
                governance_result,
                image_prompt_result=image_prompt_result,
                video_script_result=video_script_result,
            )
            if campaign_assets:
                seed_assets.update(campaign_assets)
            asset_request["assets"] = seed_assets
            try:
                asset_coordination_result = self.asset_coordinator.coordinate(asset_request)
                stage_timings["asset_coordination"] = round(perf_counter() - asset_started, 6)
            except Exception as exc:  # pragma: no cover - defensive fallback
                warning = f"Asset coordination failed: {exc}"
                log_warning(self.logger, warning)
                asset_coordination_result = {
                    "success": False,
                    "brand": normalized_request["brand"],
                    "campaign_type": campaign_type,
                    "objective": normalized_request.get("objective", ""),
                    "asset_plan": {},
                    "asset_requirements": {},
                    "assets": {},
                    "missing_assets": [],
                    "validation_result": {"valid": False, "warnings": [warning], "errors": [warning]},
                    "metadata": {"brand": normalized_request["brand"], "campaign_type": campaign_type},
                    "warnings": [warning],
                    "errors": [warning],
                    "export_paths": {},
                }
            asset_plan = dict(asset_coordination_result.get("asset_plan") or {})
            asset_requirements = dict(asset_coordination_result.get("asset_requirements") or {})
            missing_assets = list(asset_coordination_result.get("missing_assets") or [])
            asset_export_paths = dict(asset_coordination_result.get("export_paths") or {})

        output_metadata = build_output_metadata(
            brand=normalized_request["brand"],
            platform=normalized_request["platform"],
            content_type=normalized_request["content_type"],
            objective=normalized_request.get("objective", ""),
            audience=normalized_request.get("audience", ""),
            location=normalized_request.get("location", ""),
            property_type=normalized_request.get("property_type", ""),
            model=str(metadata.get("model", "")),
            provider=str(metadata.get("provider", "")),
            validation_status=validation_status,
            export_paths=exported_files,
        )
        stage_timings.setdefault("export", 0.0)

        metadata.update(
            {
                "brand_context_loaded": True,
                "generated": True,
                "parser_warnings": parsed_output.get("parser_warnings", []),
                "validation_status": validation_status,
                "exported": bool(exported_files),
                "adapted": bool(platform_variants),
                "approval_status": approval_status,
                "overall_quality_score": overall_quality_score,
                "campaign_composed": bool(campaign_result),
                "asset_coordinated": bool(asset_coordination_result),
                "execution": self._build_execution_metadata(execution_started_at, stage_timings, success=True, stage="completed", model=str(metadata.get("model", "")), provider=str(metadata.get("provider", ""))),
            }
        )
        asset_warnings = list(asset_coordination_result.get("warnings", [])) if isinstance(asset_coordination_result, dict) else []
        asset_errors = list(asset_coordination_result.get("errors", [])) if isinstance(asset_coordination_result, dict) else []
        video_script_warnings = list(video_script_result.get("warnings", [])) if isinstance(video_script_result, dict) else []
        video_script_errors = list(video_script_result.get("errors", [])) if isinstance(video_script_result, dict) else []
        result = self.build_result(
            success=True,
            request=normalized_request,
            context=context,
            prompt_payload=prompt_payload,
            ai_response=ai_response,
            parsed_output=parsed_output,
            formatted_output=formatted_output,
            validation_result=validation_result,
            image_prompt_result=image_prompt_result,
            enhanced_image_prompt=enhanced_image_prompt,
            negative_prompt=image_negative_prompt,
            visual_style=image_visual_style,
            cinematic_rules_applied=cinematic_rules_applied,
            image_prompt_validation=image_prompt_validation,
            video_script_result=video_script_result,
            video_type=video_type,
            video_duration=video_duration,
            scene_sequence=scene_sequence,
            storyboard=storyboard,
            voiceover=voiceover,
            camera_direction=camera_direction,
            music_mood=music_mood,
            video_script_validation=video_script_validation,
            adaptation_result=adaptation_result,
            platform_variants=platform_variants,
            governance_result=governance_result,
            approval_status=approval_status,
            overall_quality_score=overall_quality_score,
            governance_warnings=governance_warnings,
            governance_errors=governance_errors,
            campaign_result=campaign_result,
            campaign_strategy=campaign_strategy,
            campaign_assets=campaign_assets,
            campaign_governance_summary=campaign_governance_summary,
            campaign_export_paths=campaign_export_paths,
            asset_coordination_result=asset_coordination_result,
            asset_plan=asset_plan,
            asset_requirements=asset_requirements,
            missing_assets=missing_assets,
            asset_export_paths=asset_export_paths,
            execution_report=execution_report,
            governance_report=governance_report,
            campaign_report=campaign_report,
            asset_report=asset_report,
            export_report=export_report,
            consolidated_report=consolidated_report,
            report_export_paths=report_export_paths,
            rendered_markdown=rendered_markdown,
            rendered_text=rendered_text,
            exported_files=exported_files,
            output_metadata=output_metadata,
            metadata=metadata,
            error=None,
            warnings=list(ai_response.get("metadata", {}).get("warnings", []))
            + output_warnings
            + output_errors
            + video_script_warnings
            + video_script_errors
            + token_warnings
            + token_errors
            + governance_warnings
            + governance_errors
            + asset_warnings
            + asset_errors,
        )
        log_context(self.logger, f"Final result ready for {normalized_request['brand']}/{normalized_request['content_type']}")
        return result

    def _can_generate_live(self) -> bool:
        """Return whether live generation can proceed."""

        if not self.config.default_generation_setting("enable_live_generation", True):
            return False
        return self.client.validate_configuration()

    def _normalize_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Normalize request fields and apply defaults."""

        normalized = dict(request or {})
        normalized["brand"] = normalize_key(str(normalized.get("brand") or self.config.default_brand))
        normalized["platform"] = normalize_key(str(normalized.get("platform") or self.config.default_platform))
        normalized["content_type"] = normalize_key(str(normalized.get("content_type") or self.config.default_content_type))
        normalized.setdefault("objective", "")
        normalized.setdefault("audience", "")
        normalized.setdefault("location", "")
        normalized.setdefault("property_type", "")
        normalized.setdefault("extra_notes", "")
        normalized.setdefault("visual_style", self.config.default_visual_style)
        normalized.setdefault("image_type", "social_media_visual")
        normalized.setdefault("aspect_ratio", self.config.default_image_aspect_ratio)
        normalized.setdefault("video_type", self.config.default_video_type)
        normalized.setdefault("duration", self.config.default_video_duration)
        normalized.setdefault("tone", "premium but approachable")
        normalized["report"] = bool(normalized.get("report", False))
        normalized["report_json"] = bool(normalized.get("report_json", False))
        normalized["report_markdown"] = bool(normalized.get("report_markdown", False))
        normalized["report_export"] = bool(normalized.get("report_export", False))
        return normalized

    def _build_extra_context(self, context: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        """Assemble extra prompt context while preserving structured metadata."""

        return {
            "context_summary": context.get("summary", {}),
            "combined_context": context.get("combined_context", ""),
            "storytelling_context": context.get("storytelling_context", ""),
            "detected_categories": context.get("detected_categories", []),
            "context_warnings": context.get("warnings", []),
            "extra_notes": request.get("extra_notes", ""),
        }

    def _build_metadata(self, request: dict[str, Any], context: dict[str, Any], prompt_payload: dict[str, Any]) -> dict[str, Any]:
        """Build observability metadata for the pipeline result."""

        return {
            "brand": request["brand"],
            "platform": request["platform"],
            "content_type": request["content_type"],
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "video_type": request.get("video_type", ""),
            "duration": request.get("duration", ""),
            "tone": request.get("tone", ""),
            "context_summary": context.get("summary", {}),
            "detected_categories": context.get("detected_categories", []),
            "prompt_summary": prompt_payload.get("prompt_summary", ""),
            "prompt_version": prompt_payload.get("prompt_version", ""),
            "role_strategy": prompt_payload.get("role_strategy", ""),
            "estimated_tokens": None,
            "cost_estimate": None,
        }

    def _base_metadata(self, request: dict[str, Any]) -> dict[str, Any]:
        """Build minimal metadata for failure cases before context loads."""

        return {
            "brand": request["brand"],
            "platform": request["platform"],
            "content_type": request["content_type"],
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "video_type": request.get("video_type", ""),
            "duration": request.get("duration", ""),
            "tone": request.get("tone", ""),
            "estimated_tokens": None,
            "cost_estimate": None,
        }

    def _empty_context_summary(self, brand: str, bundle: BrandKnowledge | None, error: str) -> dict[str, Any]:
        """Build a minimal context summary for failure cases."""

        summary = {
            "brand": brand,
            "brand_root": self.config.brands_root,
            "loaded": False,
            "error": error,
            "detected_categories": [],
            "warnings": [],
            "summary": {},
        }
        if bundle is not None:
            summary["warnings"] = list(bundle.warnings)
        return summary

    def _build_campaign_assets(
        self,
        request: dict[str, Any],
        formatted_output: dict[str, Any] | None,
        platform_variants: dict[str, Any],
        governance_result: dict[str, Any] | None,
        image_prompt_result: dict[str, Any] | None = None,
        video_script_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build deterministic campaign seed assets from existing outputs."""

        if not isinstance(formatted_output, dict) or not formatted_output:
            return {}

        asset_type = str(request.get("content_type", "")).strip()
        if asset_type == "video_script":
            asset_type = "reel_script"
        asset_status = self._campaign_asset_status(governance_result)
        platform_variant = {}
        if isinstance(platform_variants, dict):
            platform_variant = dict(platform_variants.get(normalize_key(str(request.get("platform", "")))) or {})
        seed = {
            asset_type: {
                "asset_type": asset_type,
                "platform": request.get("platform", ""),
                "purpose": request.get("objective", ""),
                "content": formatted_output,
                "formatted_output": formatted_output,
                "platform_variant": platform_variant,
                "governance_result": governance_result or {},
                "metadata": {
                    "brand": request.get("brand", ""),
                    "audience": request.get("audience", ""),
                    "location": request.get("location", ""),
                    "objective": request.get("objective", ""),
                },
                "status": asset_status,
            }
        }
        if asset_type == "image_prompt" and isinstance(image_prompt_result, dict) and image_prompt_result:
            seed[asset_type].update(
                {
                    "subject": image_prompt_result.get("metadata", {}).get("image_type", "") if isinstance(image_prompt_result.get("metadata"), dict) else "",
                    "composition": image_prompt_result.get("composition_style", ""),
                    "lighting": image_prompt_result.get("lighting_style", ""),
                    "style": image_prompt_result.get("visual_style", ""),
                    "aspect_ratio": image_prompt_result.get("aspect_ratio", ""),
                    "negative_prompt": image_prompt_result.get("negative_prompt", ""),
                    "platform_use": request.get("platform", ""),
                    "visual_direction": image_prompt_result.get("prompt", ""),
                    "enhanced_image_prompt": image_prompt_result.get("prompt", ""),
                    "image_prompt_result": image_prompt_result,
                    "validation": image_prompt_result.get("validation", {}),
                    "camera_direction": image_prompt_result.get("camera_direction", ""),
                }
            )
        if asset_type == "reel_script" and isinstance(video_script_result, dict) and video_script_result:
            seed[asset_type].update(
                {
                    "hook": video_script_result.get("hook", ""),
                    "script": video_script_result.get("script", ""),
                    "scenes": list(video_script_result.get("scene_sequence", [])) if isinstance(video_script_result.get("scene_sequence"), list) else [],
                    "storyboard": list(video_script_result.get("storyboard", [])) if isinstance(video_script_result.get("storyboard"), list) else [],
                    "voiceover_direction": video_script_result.get("voiceover", ""),
                    "cta": video_script_result.get("cta", ""),
                    "visual_direction": video_script_result.get("script", "") or video_script_result.get("hook", ""),
                    "duration": video_script_result.get("duration", ""),
                    "camera_direction": video_script_result.get("camera_direction", ""),
                    "music_mood": video_script_result.get("music_mood", ""),
                    "video_script_result": video_script_result,
                    "validation": video_script_result.get("validation", {}),
                }
            )
        return seed

    def _campaign_asset_status(self, governance_result: dict[str, Any] | None) -> str:
        """Derive a campaign asset status from governance output."""

        if not isinstance(governance_result, dict):
            return "warning"
        status = str(governance_result.get("status", "")).lower()
        if status == "approved":
            return "approved"
        if status == "approved_with_warnings":
            return "warning"
        if status == "rejected":
            return "rejected"
        if status in {"needs_review", "warning"}:
            return "warning"
        return "warning"

    def _build_asset_seed(
        self,
        request: dict[str, Any],
        formatted_output: dict[str, Any] | None,
        platform_variants: dict[str, Any],
        governance_result: dict[str, Any] | None,
        image_prompt_result: dict[str, Any] | None = None,
        video_script_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build deterministic seed assets for asset coordination."""

        if not isinstance(formatted_output, dict) or not formatted_output:
            return {}

        asset_type = normalize_asset_type(str(request.get("content_type", "")))
        platform_variant = {}
        if isinstance(platform_variants, dict):
            platform_variant = dict(platform_variants.get(normalize_key(str(request.get("platform", "")))) or {})
        seed = {
            asset_type: {
                "asset_type": asset_type,
                "platform": request.get("platform", ""),
                "purpose": request.get("objective", ""),
                "content": formatted_output,
                "formatted_output": formatted_output,
                "platform_variant": platform_variant,
                "governance_result": governance_result or {},
                "metadata": {
                    "brand": request.get("brand", ""),
                    "audience": request.get("audience", ""),
                    "location": request.get("location", ""),
                    "objective": request.get("objective", ""),
                "campaign_type": request.get("campaign_type", ""),
                },
                "status": self._campaign_asset_status(governance_result),
            }
        }
        if asset_type == "image_prompt" and isinstance(image_prompt_result, dict) and image_prompt_result:
            seed[asset_type].update(
                {
                    "subject": image_prompt_result.get("metadata", {}).get("image_type", "") if isinstance(image_prompt_result.get("metadata"), dict) else "",
                    "composition": image_prompt_result.get("composition_style", ""),
                    "lighting": image_prompt_result.get("lighting_style", ""),
                    "style": image_prompt_result.get("visual_style", ""),
                    "aspect_ratio": image_prompt_result.get("aspect_ratio", ""),
                    "negative_prompt": image_prompt_result.get("negative_prompt", ""),
                    "platform_use": request.get("platform", ""),
                    "visual_direction": image_prompt_result.get("prompt", ""),
                    "enhanced_image_prompt": image_prompt_result.get("prompt", ""),
                    "image_prompt_result": image_prompt_result,
                    "validation": image_prompt_result.get("validation", {}),
                    "camera_direction": image_prompt_result.get("camera_direction", ""),
                }
            )
        if asset_type == "reel_script" and isinstance(video_script_result, dict) and video_script_result:
            seed[asset_type].update(
                {
                    "hook": video_script_result.get("hook", ""),
                    "script": video_script_result.get("script", ""),
                    "scenes": list(video_script_result.get("scene_sequence", [])) if isinstance(video_script_result.get("scene_sequence"), list) else [],
                    "storyboard": list(video_script_result.get("storyboard", [])) if isinstance(video_script_result.get("storyboard"), list) else [],
                    "voiceover_direction": video_script_result.get("voiceover", ""),
                    "cta": video_script_result.get("cta", ""),
                    "visual_direction": video_script_result.get("script", "") or video_script_result.get("hook", ""),
                    "duration": video_script_result.get("duration", ""),
                    "camera_direction": video_script_result.get("camera_direction", ""),
                    "music_mood": video_script_result.get("music_mood", ""),
                    "video_script_result": video_script_result,
                    "validation": video_script_result.get("validation", {}),
                }
            )
        return seed

    def _build_image_prompt_request(
        self,
        request: dict[str, Any],
        context: dict[str, Any],
        parsed_output: dict[str, Any],
        formatted_output: dict[str, Any] | None,
        creative_direction_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a prompt-engine request for image prompt generation."""

        request_payload = dict(request)
        request_payload["content_type"] = "image_prompt"
        request_payload["image_type"] = request.get("image_type") or request.get("content_type") or "social_media_visual"
        request_payload["aspect_ratio"] = request.get("aspect_ratio") or self.config.default_image_aspect_ratio
        request_payload["visual_style"] = request.get("visual_style") or self.config.default_visual_style
        if not request_payload.get("creative_direction"):
            request_payload["creative_direction"] = (
                self._extract_image_prompt_seed(formatted_output)
                or self._extract_image_prompt_seed(parsed_output)
                or str(context.get("summary", {}).get("combined_context", "")).strip()
                or request.get("extra_notes", "")
            )
        request_payload["enable_negative_prompts"] = self.config.enable_negative_prompts
        request_payload["enable_cinematic_enhancement"] = self.config.enable_cinematic_enhancement
        request_payload["creative_direction_result"] = dict(creative_direction_result or {}) if isinstance(creative_direction_result, dict) else {}
        return request_payload

    def _build_video_script_request(
        self,
        request: dict[str, Any],
        context: dict[str, Any],
        parsed_output: dict[str, Any],
        formatted_output: dict[str, Any] | None,
        creative_direction_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a video script engine request from structured pipeline data."""

        request_payload = dict(request)
        request_payload["content_type"] = "video_script"
        request_payload["video_type"] = request.get("video_type") or self.config.default_video_type
        request_payload["duration"] = request.get("duration") or self.config.default_video_duration
        request_payload["tone"] = request.get("tone") or "premium but approachable"
        request_payload["visual_style"] = request.get("visual_style") or self.config.default_visual_style
        if not request_payload.get("creative_direction"):
            request_payload["creative_direction"] = (
                self._extract_video_script_seed(formatted_output)
                or self._extract_video_script_seed(parsed_output)
                or str(context.get("summary", {}).get("combined_context", "")).strip()
                or request.get("extra_notes", "")
            )
        request_payload["enable_storyboard_generation"] = self.config.enable_storyboard_generation
        request_payload["creative_direction_result"] = dict(creative_direction_result or {}) if isinstance(creative_direction_result, dict) else {}
        return request_payload

    def _build_creative_direction_request(self, request: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Build a creative direction request from the pipeline request payload."""

        request_payload = dict(request)
        request_payload["content_type"] = "creative_direction"
        request_payload["campaign_type"] = request.get("campaign_type") or self.config.default_campaign_type
        request_payload["creative_direction_type"] = request.get("creative_direction_type") or self.config.default_creative_direction_type
        request_payload["visual_style"] = request.get("visual_style") or self.config.default_visual_identity
        request_payload["platforms"] = list(request.get("platforms") or [request.get("platform", self.config.default_platform)])
        request_payload["creative_direction"] = (
            request.get("creative_direction")
            or request.get("extra_notes")
            or str(context.get("summary", {}).get("combined_context", "")).strip()
        )
        request_payload["extra_notes"] = request.get("extra_notes") or str(context.get("summary", {}).get("combined_context", "")).strip()
        return request_payload

    def _extract_image_prompt_seed(self, payload: dict[str, Any] | None) -> str:
        """Extract a fallback prompt seed from parsed or formatted content."""

        if not isinstance(payload, dict):
            return ""
        for key in ("creative_direction", "visual_direction", "prompt", "content", "caption", "description", "summary"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _extract_video_script_seed(self, payload: dict[str, Any] | None) -> str:
        """Extract a fallback seed from parsed or formatted video content."""

        if not isinstance(payload, dict):
            return ""
        for key in ("creative_direction", "hook", "script", "voiceover", "prompt", "content", "caption", "description", "summary"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _build_execution_metadata(
        self,
        started_at: datetime,
        stage_timings: dict[str, float],
        *,
        success: bool,
        stage: str,
        error: str | None = None,
        model: str = "",
        provider: str = "",
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Build execution metadata for reporting and diagnostics."""

        ended_at = datetime.now(timezone.utc)
        total_duration = round((ended_at - started_at).total_seconds(), 6)
        return {
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "duration_seconds": total_duration,
            "stages": dict(stage_timings),
            "completed_stage": stage,
            "success": success,
            "error": error,
            "model": model,
            "provider": provider,
            "dry_run": dry_run,
        }

    def _build_token_tracking(
        self,
        *,
        request: dict[str, Any],
        prompt_payload: dict[str, Any] | None,
        ai_response: dict[str, Any] | None,
        parsed_output: dict[str, Any] | None,
        metadata: dict[str, Any],
        execution_id: str,
    ) -> dict[str, Any]:
        """Build token usage records and aggregated summaries."""

        if not self.config.enable_token_tracking:
            return {
                "token_usage": None,
                "execution_token_summary": None,
                "module_token_summary": None,
                "provider_token_summary": None,
                "estimated_token_usage": None,
                "warnings": [],
                "errors": [],
            }

        base_metadata = {
            **metadata,
            "brand": request.get("brand", ""),
            "platform": request.get("platform", ""),
            "content_type": request.get("content_type", ""),
            "objective": request.get("objective", ""),
            "audience": request.get("audience", ""),
            "location": request.get("location", ""),
            "property_type": request.get("property_type", ""),
            "execution_id": execution_id,
            "module": request.get("content_type", ""),
            "operation": "generation",
            "campaign_id": str(request.get("campaign_type", "") or request.get("objective", "") or ""),
            "asset_type": request.get("content_type", ""),
            "provider": metadata.get("provider", ""),
            "model": metadata.get("model", ""),
        }

        usage_record = self.token_tracker.build_unavailable_result(metadata=base_metadata)
        if isinstance(ai_response, dict):
            token_usage = ai_response.get("token_usage")
            if isinstance(token_usage, dict) and token_usage:
                usage_record = self.token_tracker.record_generation(token_usage, metadata=base_metadata)
            elif self.config.enable_token_estimation:
                prompt_text = ""
                if isinstance(prompt_payload, dict):
                    prompt_text = f"{prompt_payload.get('system_prompt', '')}\n{prompt_payload.get('user_prompt', '')}".strip()
                generated_text = str(ai_response.get("content", "") or "")
                usage_record = self.token_tracker.record_estimated_usage(
                    input_text=prompt_text,
                    output_text=generated_text,
                    metadata=base_metadata,
                )

        records = [usage_record]
        execution_summary = self.token_tracker.aggregate_execution(records)
        module_summary = self.token_tracker.aggregator.aggregate_by_module(records)
        provider_summary = self.token_tracker.aggregator.aggregate_by_provider(records)
        estimated_token_usage = usage_record if bool(usage_record.get("estimated")) else None

        if not usage_record.get("estimated") and usage_record.get("source") == "unavailable":
            warnings = list(usage_record.get("warnings", []))
            if "Token usage unavailable." not in warnings:
                warnings.append("Token usage unavailable.")
            usage_record["warnings"] = warnings

        return {
            "token_usage": usage_record,
            "execution_token_summary": execution_summary,
            "module_token_summary": module_summary,
            "provider_token_summary": provider_summary,
            "estimated_token_usage": estimated_token_usage,
            "warnings": list(usage_record.get("warnings", [])),
            "errors": list(usage_record.get("errors", [])),
        }

    def _attach_reporting(self, result: dict[str, Any], request: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """Attach optional reporting payloads to a pipeline result."""

        if not self._should_generate_reports(request):
            return result

        report_bundle = self.reporting_engine.generate(
            result,
            export=bool(self.config.enable_report_export or request.get("report_export")),
            formats=list(self.config.report_formats),
            render_format="json" if request.get("report_json") else "markdown" if request.get("report_markdown") else "terminal",
            report_name=f"{request.get('brand', '')}_{request.get('content_type', '')}",
        )
        metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
        report_metadata = report_bundle.get("metadata", {})
        result.update(
            {
                "execution_report": report_bundle.get("execution_report"),
                "governance_report": report_bundle.get("governance_report"),
                "campaign_report": report_bundle.get("campaign_report"),
                "asset_report": report_bundle.get("asset_report"),
                "export_report": report_bundle.get("export_report"),
                "consolidated_report": report_bundle.get("consolidated_report"),
                "report_export_paths": report_bundle.get("exported_files", {}),
                "image_prompt_report": report_bundle.get("image_prompt_report", {}),
                "video_script_report": report_bundle.get("video_script_report", {}),
                "creative_direction_report": report_bundle.get("creative_direction_report", {}),
                "metadata": {**metadata, "reporting": report_metadata},
            }
        )
        return result

    def _should_generate_reports(self, request: dict[str, Any]) -> bool:
        """Return whether reporting should be generated for a request."""

        return bool(
            self.config.enable_reporting
            or request.get("report")
            or request.get("report_json")
            or request.get("report_markdown")
        )


if __name__ == "__main__":
    logger = get_logger("content_generation_pipeline_demo")
    pipeline = ContentGenerationPipeline(logger=logger)

    demo_requests = [
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "objective": "generate_leads",
            "audience": "relocation_clients",
            "location": "sant_llorenc_des_cardassar",
            "property_type": "rustic_home",
            "extra_notes": "Rustic outside, modern comfort inside, close to Manacor and beaches.",
        },
        {
            "brand": "wenzel_partner",
            "platform": "image",
            "content_type": "image_prompt",
            "objective": "create_visual_direction",
            "audience": "second_home_buyers",
            "location": "portixol",
            "property_type": "sea_view_apartment",
        },
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "property_description",
            "objective": "describe_listing",
            "audience": "luxury_buyers",
            "location": "palma_old_town",
            "property_type": "apartment",
        },
    ]

    print("Validation and pipeline demo")
    print("OpenAI configuration valid:", pipeline.client.validate_configuration())
    for request in demo_requests:
        valid, reason = pipeline.validate_request(request)
        print(f"Request valid for {request['content_type']}: {valid} {reason or ''}".strip())
        context = pipeline.load_context(request["brand"])
        print(f"Context loaded for {request['content_type']}: {context.get('loaded')}")
        prompt_result = pipeline.build_prompt(request, context)
        print(f"Prompt built for {request['content_type']}: {bool(prompt_result.get('prompt_payload'))}")
        if pipeline.client.validate_configuration():
            ai_response = pipeline.generate_ai_response(prompt_result["prompt_payload"])
            print(f"AI response success for {request['content_type']}: {ai_response.get('success')}")
            if ai_response.get("success"):
                parsed = pipeline.parse_response(ai_response)
                print(f"Parsed output keys for {request['content_type']}: {sorted(parsed.keys())}")
        else:
            print(f"Skipping live generation for {request['content_type']} because OPENAI_API_KEY is missing or the SDK is unavailable.")
        print(json.dumps(pipeline.generate(request), indent=2, ensure_ascii=False)[:3000])
