"""End-to-end AI content generation pipeline."""

from __future__ import annotations

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
from src.pipeline.pipeline_config import PipelineConfig
from src.pipeline.pipeline_result import build_failure_result, build_success_result
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
        rendered_markdown: str | None,
        rendered_text: str | None,
        exported_files: dict[str, str] | None,
        output_metadata: dict[str, Any] | None,
        metadata: dict[str, Any],
        error: str | None,
        warnings: list[str] | None = None,
    ) -> dict[str, Any]:
        """Build a structured pipeline result."""

        normalized_request = self._normalize_request(request)
        if success:
            return build_success_result(
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
                rendered_markdown=rendered_markdown,
                rendered_text=rendered_text,
                exported_files=exported_files or {},
                output_metadata=output_metadata or {},
                metadata=metadata,
                warnings=warnings or [],
            )
        return build_failure_result(
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
            rendered_markdown=rendered_markdown,
            rendered_text=rendered_text,
            exported_files=exported_files or {},
            output_metadata=output_metadata or {},
            warnings=warnings or [],
        )

    def _generate(self, request: dict[str, Any]) -> dict[str, Any]:
        """Internal orchestration for a single content generation request."""

        is_valid, validation_error = self.validate_request(request)
        normalized_request = self._normalize_request(request)
        base_metadata = self._base_metadata(normalized_request)

        if not is_valid:
            log_warning(self.logger, validation_error or "Request validation failed.")
            return self.build_result(
                success=False,
                request=normalized_request,
                context=self._empty_context_summary(normalized_request["brand"], None, validation_error or "Request validation failed."),
                prompt_payload=None,
                ai_response=None,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=base_metadata,
                error=validation_error or "Request validation failed.",
            )

        context = self.load_context(normalized_request["brand"])
        if not context.get("loaded"):
            error = context.get("error") or f"Brand context is missing for '{normalized_request['brand']}'."
            log_error(self.logger, error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=None,
                ai_response=None,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=base_metadata,
                error=error,
                warnings=context.get("warnings", []),
            )

        prompt_result = self.build_prompt(normalized_request, context)
        if prompt_result.get("errors"):
            error = "; ".join(prompt_result["errors"])
            log_error(self.logger, error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=None,
                ai_response=None,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
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
        log_context(self.logger, f"Model routed to {model_route.provider}/{model_route.model_name}")

        if not self._can_generate_live():
            error = "OpenAI API key missing or live generation disabled; skipping live generation."
            log_warning(self.logger, error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=prompt_payload,
                ai_response=None,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=metadata,
                error=error,
                warnings=[],
            )

        log_context(self.logger, f"Generating AI output for {normalized_request['brand']}/{normalized_request['content_type']}")
        ai_response = self.generate_ai_response(prompt_payload)
        if not ai_response.get("success"):
            error = str(ai_response.get("error") or "OpenAI generation failed.")
            log_error(self.logger, error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=prompt_payload,
                ai_response=ai_response,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
                rendered_markdown=None,
                rendered_text=None,
                exported_files={},
                output_metadata={},
                metadata=metadata,
                error=error,
                warnings=list(ai_response.get("metadata", {}).get("warnings", [])),
            )

        try:
            parsed_output = self.parse_response(ai_response)
        except Exception as exc:  # pragma: no cover - defensive fallback
            error = f"Response parsing failed: {exc}"
            log_error(self.logger, error)
            return self.build_result(
                success=False,
                request=normalized_request,
                context=context,
                prompt_payload=prompt_payload,
                ai_response=ai_response,
                parsed_output=None,
                formatted_output=None,
                validation_result=None,
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
        rendered_markdown = None
        rendered_text = None
        exported_files: dict[str, str] = {}
        output_metadata: dict[str, Any] = {}
        output_errors: list[str] = []
        output_warnings: list[str] = []

        if self.config.enable_output_formatting:
            try:
                formatted_output = self.formatter.format(parsed_output, normalized_request["content_type"])
            except Exception as exc:  # pragma: no cover - defensive fallback
                error = f"Output formatting failed: {exc}"
                log_error(self.logger, error)
                return self.build_result(
                    success=False,
                    request=normalized_request,
                    context=context,
                    prompt_payload=prompt_payload,
                    ai_response=ai_response,
                    parsed_output=parsed_output,
                    formatted_output=None,
                    validation_result=None,
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
                    rendered_markdown = self.renderer.render_markdown(formatted_output, normalized_request["content_type"])
                    rendered_text = self.renderer.render_text(formatted_output, normalized_request["content_type"])
                except Exception as exc:  # pragma: no cover - defensive fallback
                    error = f"Output rendering failed: {exc}"
                    log_error(self.logger, error)
                    return self.build_result(
                        success=False,
                        request=normalized_request,
                        context=context,
                        prompt_payload=prompt_payload,
                        ai_response=ai_response,
                        parsed_output=parsed_output,
                        formatted_output=formatted_output,
                        validation_result=validation_result,
                        rendered_markdown=None,
                        rendered_text=None,
                        exported_files={},
                        output_metadata={},
                        metadata=metadata,
                        error=error,
                        warnings=output_warnings,
                    )

            if self.config.enable_export:
                try:
                    exported_files = self.exporter.export(
                        brand=normalized_request["brand"],
                        content_type=normalized_request["content_type"],
                        output=formatted_output,
                        metadata=metadata,
                        validation_result=validation_result or {"valid": True, "warnings": [], "errors": []},
                        formats=list(self.config.export_formats),
                    )
                except Exception as exc:  # pragma: no cover - defensive fallback
                    log_warning(self.logger, f"Export failed: {exc}")
                    exported_files = {}

        validation_status = "passed"
        if validation_result and not validation_result.get("valid", True):
            validation_status = "failed"
        elif validation_result and validation_result.get("warnings"):
            validation_status = "warning"

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

        metadata.update(
            {
                "brand_context_loaded": True,
                "generated": True,
                "parser_warnings": parsed_output.get("parser_warnings", []),
                "validation_status": validation_status,
                "exported": bool(exported_files),
            }
        )
        result = self.build_result(
            success=True,
            request=normalized_request,
            context=context,
            prompt_payload=prompt_payload,
            ai_response=ai_response,
            parsed_output=parsed_output,
            formatted_output=formatted_output,
            validation_result=validation_result,
            rendered_markdown=rendered_markdown,
            rendered_text=rendered_text,
            exported_files=exported_files,
            output_metadata=output_metadata,
            metadata=metadata,
            error=None,
            warnings=list(ai_response.get("metadata", {}).get("warnings", [])) + output_warnings + output_errors,
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
