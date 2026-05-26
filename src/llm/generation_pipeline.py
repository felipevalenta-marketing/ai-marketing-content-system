"""End-to-end generation pipeline from structured prompt payload to output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.llm.llm_router import LLMRouter
from src.llm.openai_client import OpenAIClient
from src.llm.response_parser import ResponseParser
from src.utils.logger import get_logger, log_context, log_error, log_warning


@dataclass(frozen=True)
class GenerationResult:
    """Structured final output from the generation pipeline."""

    success: bool
    provider: str
    model: str
    content: str
    hashtags: list[str]
    cta: str | None
    json: dict[str, Any] | None
    raw_content: str
    parser_warnings: list[str]
    raw_response: Any
    metadata: dict[str, Any]
    error: str | None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the generation result."""

        return {
            "success": self.success,
            "provider": self.provider,
            "model": self.model,
            "content": self.content,
            "hashtags": self.hashtags,
            "cta": self.cta,
            "json": self.json,
            "raw_content": self.raw_content,
            "parser_warnings": self.parser_warnings,
            "raw_response": self.raw_response,
            "metadata": self.metadata,
            "error": self.error,
            "warnings": self.warnings,
        }


class GenerationPipeline:
    """Coordinate routing, generation, parsing, and structured result assembly."""

    def __init__(
        self,
        brands_root: str | Path | None = None,
        logger: Any | None = None,
        router: LLMRouter | None = None,
        client: OpenAIClient | None = None,
        parser: ResponseParser | None = None,
    ) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.router = router or LLMRouter(logger=self.logger)
        self.client = client or OpenAIClient(logger=self.logger)
        self.parser = parser or ResponseParser(logger=self.logger)

    def generate(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        """Generate structured output from a prompt payload."""

        return self._generate(prompt_payload)

    def generate_for_content_type(self, prompt_payload: dict[str, Any], content_type: str) -> dict[str, Any]:
        """Generate output for an explicit content type override."""

        merged_payload = dict(prompt_payload)
        merged_payload["content_type"] = content_type
        return self._generate(merged_payload)

    def _generate(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        """Run the generation flow with validation and graceful failure handling."""

        validation_errors = self._validate_prompt_payload(prompt_payload)
        metadata = self._build_metadata(prompt_payload)
        if validation_errors:
            log_warning(self.logger, "; ".join(validation_errors))
            return self._failure_payload(
                prompt_payload=prompt_payload,
                metadata=metadata,
                message="; ".join(validation_errors),
            )

        content_type = str(prompt_payload.get("content_type", "")).strip()
        route = self.router.route(
            content_type=content_type,
            provider=str(metadata.get("provider") or "openai"),
            preferred_model=str(metadata.get("model") or "") or None,
            platform=str(prompt_payload.get("platform") or metadata.get("platform") or ""),
        )
        metadata.update(
            {
                "provider": route.provider,
                "model": route.model_name,
                "route_reason": route.route_reason,
                "routing": route.to_dict(),
            }
        )

        client_response = self.client.generate_text({
            **prompt_payload,
            "metadata": {
                **metadata,
                "provider": route.provider,
                "model": route.model_name,
            },
        })

        if not client_response.get("success"):
            log_error(self.logger, str(client_response.get("error") or "OpenAI generation failed."))
            return self._result_from_client_failure(prompt_payload, metadata, client_response)

        parsed = self.parser.parse_text_response(client_response)
        warnings = list(client_response.get("metadata", {}).get("warnings", []))
        parser_warnings = list(parsed.get("parser_warnings", []))
        if parser_warnings:
            log_warning(self.logger, "; ".join(parser_warnings))

        log_context(self.logger, f"Generated {metadata.get('brand', '')}/{route.provider}/{route.model_name}/{content_type}")
        return GenerationResult(
            success=True,
            provider=route.provider,
            model=route.model_name,
            content=parsed.get("content", ""),
            hashtags=list(parsed.get("hashtags", [])),
            cta=parsed.get("cta"),
            json=parsed.get("json"),
            raw_content=parsed.get("raw_content", ""),
            parser_warnings=parser_warnings,
            raw_response=client_response.get("raw_response"),
            metadata={
                **metadata,
                "context_used": prompt_payload.get("context_used", []),
                "platform_rules": prompt_payload.get("platform_rules", []),
                "parser": {
                    "parser_warnings": parser_warnings,
                },
            },
            error=None,
            warnings=warnings,
        ).to_dict()

    def _validate_prompt_payload(self, prompt_payload: dict[str, Any]) -> list[str]:
        """Validate the required prompt payload fields."""

        errors: list[str] = []
        if not isinstance(prompt_payload, dict):
            return ["Prompt payload must be a dictionary."]

        if not str(prompt_payload.get("system_prompt", "")).strip():
            errors.append("Missing system_prompt.")
        if not str(prompt_payload.get("user_prompt", "")).strip():
            errors.append("Missing user_prompt.")
        if not str(prompt_payload.get("content_type", "")).strip():
            errors.append("Missing content_type.")
        if not str(prompt_payload.get("brand", "")).strip():
            errors.append("Missing brand.")
        return errors

    def _build_metadata(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        """Collect observability metadata from the prompt payload."""

        metadata = dict(prompt_payload.get("metadata") or prompt_payload.get("orchestration_metadata") or {})
        metadata.setdefault("brand", prompt_payload.get("brand", ""))
        metadata.setdefault("content_type", prompt_payload.get("content_type", ""))
        metadata.setdefault("context_used", prompt_payload.get("context_used", []))
        metadata.setdefault("platform_rules", prompt_payload.get("platform_rules", []))
        metadata.setdefault("estimated_tokens", None)
        metadata.setdefault("cost_estimate", None)
        metadata.setdefault("provider", "openai")
        metadata.setdefault("model", "")
        return metadata

    def _result_from_client_failure(
        self,
        prompt_payload: dict[str, Any],
        metadata: dict[str, Any],
        client_response: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert a client failure into a structured generation result."""

        return GenerationResult(
            success=False,
            provider=str(client_response.get("provider") or metadata.get("provider") or "openai"),
            model=str(client_response.get("model") or metadata.get("model") or ""),
            content="",
            hashtags=[],
            cta=None,
            json=None,
            raw_content="",
            parser_warnings=[],
            raw_response=client_response.get("raw_response"),
            metadata={**metadata, "prompt": prompt_payload},
            error=str(client_response.get("error") or "Generation failed."),
            warnings=list(client_response.get("metadata", {}).get("warnings", [])),
        ).to_dict()

    def _failure_payload(self, prompt_payload: dict[str, Any], metadata: dict[str, Any], message: str) -> dict[str, Any]:
        """Build a structured failure response."""

        return GenerationResult(
            success=False,
            provider=str(metadata.get("provider") or "openai"),
            model=str(metadata.get("model") or ""),
            content="",
            hashtags=[],
            cta=None,
            json=None,
            raw_content="",
            parser_warnings=[],
            raw_response=None,
            metadata={**metadata, "prompt": prompt_payload},
            error=message,
            warnings=[],
        ).to_dict()


if __name__ == "__main__":
    from src.prompts.prompt_builder import PromptBuilder

    logger = get_logger("generation_pipeline_demo")
    builder = PromptBuilder(logger=logger)
    pipeline = GenerationPipeline(logger=logger)
    brands = builder.loader.detect_brands()
    brand_name = "wenzel_partner" if "wenzel_partner" in brands else (brands[0] if brands else "")

    if not brand_name:
        print("No brands available for generation demo.")
    else:
        instagram_prompt = builder.build_prompt(
            {
                "brand": brand_name,
                "platform": "instagram",
                "content_type": "instagram_reel",
                "objective": "generate_leads",
                "audience": "relocation_clients",
                "location": "santa_catalina",
                "property_type": "apartment",
            }
        )
        image_prompt = builder.build_prompt(
            {
                "brand": brand_name,
                "platform": "image",
                "content_type": "image_prompt",
                "objective": "create_visual_direction",
                "audience": "second_home_buyers",
                "location": "portixol",
                "property_type": "sea_view_apartment",
            }
        )

        print("OpenAI configuration valid:", pipeline.client.validate_configuration())
        print("Instagram generation result:")
        print(pipeline.generate(instagram_prompt))
        print("Image prompt generation result:")
        print(pipeline.generate(image_prompt))
