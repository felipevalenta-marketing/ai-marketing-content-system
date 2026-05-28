"""OpenAI Responses API client for the generation layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import json
import os
import time

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        """Fallback no-op when python-dotenv is unavailable."""

        return False

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency
    OpenAI = None

from src.llm.model_registry import (
    estimate_tokens,
    get_env_default_max_output_tokens,
    get_env_default_model,
    get_env_default_temperature,
    is_supported_model,
)
from src.utils.logger import get_logger, log_context, log_error, log_warning


MAX_OPENAI_METADATA_KEYS = 16
MAX_METADATA_VALUE_LENGTH = 120
PRIORITY_METADATA_FIELDS = (
    "brand",
    "platform",
    "content_type",
    "objective",
    "model",
    "provider",
    "request_id",
    "generation_mode",
    "template_version",
    "route",
    "pipeline_stage",
    "user_locale",
    "target_audience",
    "campaign_type",
    "asset_type",
    "timestamp",
)


@dataclass(frozen=True)
class OpenAIClientConfig:
    """Runtime configuration for the OpenAI client."""

    api_key: str | None
    default_model: str
    default_temperature: float
    default_max_output_tokens: int
    timeout_seconds: int
    app_env: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the configuration without secrets."""

        return {
            "default_model": self.default_model,
            "default_temperature": self.default_temperature,
            "default_max_output_tokens": self.default_max_output_tokens,
            "timeout_seconds": self.timeout_seconds,
            "app_env": self.app_env,
            "api_key_present": bool(self.api_key),
        }


@dataclass(frozen=True)
class OpenAIGenerationResult:
    """Structured result returned by the client."""

    success: bool
    provider: str
    model: str
    content: str
    raw_response: Any
    metadata: dict[str, Any]
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize the response."""

        return {
            "success": self.success,
            "provider": self.provider,
            "model": self.model,
            "content": self.content,
            "raw_response": self.raw_response,
            "metadata": self.metadata,
            "error": self.error,
        }


class OpenAIClient:
    """OpenAI Responses API wrapper with safe initialization and fallbacks."""

    def __init__(self, config: OpenAIClientConfig | None = None, logger: Any | None = None) -> None:
        load_dotenv()
        self.logger = logger or get_logger(self.__class__.__name__)
        self.config = config or self._load_config_from_env()
        self._client = self._initialize_client()

    def validate_configuration(self) -> bool:
        """Validate that the client is ready for live generation."""

        if OpenAI is None:
            log_error(self.logger, "OpenAI SDK is not installed.")
            return False
        if not self.config.api_key:
            log_error(self.logger, "OPENAI_API_KEY is missing.")
            return False
        if self._client is None:
            log_error(self.logger, "OpenAI client could not be initialized.")
            return False
        if not is_supported_model(self.config.default_model, provider="openai"):
            log_error(self.logger, f"Unsupported default model configuration: {self.config.default_model}.")
            return False
        return True

    def health_check(self) -> bool:
        """Return whether the client is configured and importable."""

        return self.validate_configuration() and self._client is not None

    def generate_text(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        """Generate text from a prompt payload produced by the prompt builder."""

        system_prompt = str(prompt_payload.get("system_prompt", "")).strip()
        user_prompt = str(prompt_payload.get("user_prompt", "")).strip()
        metadata = self._build_metadata(prompt_payload)
        content_type = str(prompt_payload.get("content_type", "")).strip()
        model_name = self._resolve_model_name(metadata.get("model"))
        temperature = self._coerce_float(metadata.get("temperature"), self.config.default_temperature)
        max_output_tokens = self._coerce_int(metadata.get("max_output_tokens"), self.config.default_max_output_tokens)

        if not system_prompt or not user_prompt:
            return self._failure(
                model_name=model_name,
                metadata=metadata,
                message="Prompt payload is missing system_prompt or user_prompt.",
            )

        if not self.validate_configuration():
            return self._failure(
                model_name=model_name,
                metadata=metadata,
                message="OpenAI client is not configured. Set OPENAI_API_KEY to enable live generation.",
            )

        provider_hint = metadata.get("provider", "openai")
        log_context(self.logger, f"Starting generation for {content_type} with {provider_hint}/{model_name}")
        return self.generate_from_messages(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            metadata={
                **metadata,
                "content_type": content_type,
                "estimated_tokens": metadata.get("estimated_tokens"),
                "cost_estimate": metadata.get("cost_estimate"),
            },
            model=model_name,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    def generate_from_messages(
        self,
        system_prompt: str,
        user_prompt: str,
        metadata: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_output_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Generate a response using the Responses API."""

        metadata = dict(metadata or {})
        model_name = self._resolve_model_name(model or metadata.get("model"))
        temp = self._coerce_float(temperature if temperature is not None else metadata.get("temperature"), self.config.default_temperature)
        max_tokens = self._coerce_int(
            max_output_tokens if max_output_tokens is not None else metadata.get("max_output_tokens"),
            self.config.default_max_output_tokens,
        )

        if not system_prompt.strip() or not user_prompt.strip():
            return self._failure(model_name=model_name, metadata=metadata, message="System and user prompts must not be empty.")

        if not self.validate_configuration():
            return self._failure(model_name=model_name, metadata=metadata, message="OpenAI client configuration is invalid.")

        start_time = time.perf_counter()
        try:
            sanitized_metadata = self._sanitize_metadata(metadata)
            response = self._client.responses.create(  # type: ignore[union-attr]
                model=model_name,
                instructions=system_prompt,
                input=user_prompt,
                temperature=temp,
                max_output_tokens=max_tokens,
                metadata=sanitized_metadata,
            )
            content = self._extract_response_text(response)
            elapsed = time.perf_counter() - start_time
            response_dict = self._serialize_response(response)
            token_estimate = estimate_tokens(f"{system_prompt}\n{user_prompt}", model_name)
            result_metadata = {
                **metadata,
                "provider": "openai",
                "model": model_name,
                "temperature": temp,
                "max_output_tokens": max_tokens,
                "estimated_tokens": token_estimate,
                "cost_estimate": None,
                "latency_seconds": round(elapsed, 4),
            }
            log_context(self.logger, f"Generation success for {model_name}")
            return OpenAIGenerationResult(
                success=True,
                provider="openai",
                model=model_name,
                content=content,
                raw_response=response_dict,
                metadata=result_metadata,
                error=None,
            ).to_dict()
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            log_error(self.logger, f"OpenAI generation failed: {exc}")
            return self._failure(model_name=model_name, metadata=metadata, message=self._sanitize_error(str(exc)))

    def _initialize_client(self) -> Any | None:
        """Initialize the OpenAI SDK client safely."""

        if OpenAI is None or not self.config.api_key:
            return None
        return OpenAI(api_key=self.config.api_key, timeout=self.config.timeout_seconds)

    def _load_config_from_env(self) -> OpenAIClientConfig:
        """Load configuration from environment variables."""

        return OpenAIClientConfig(
            api_key=os.getenv("OPENAI_API_KEY", "").strip() or None,
            default_model=os.getenv("OPENAI_MODEL_DEFAULT", get_env_default_model()).strip() or get_env_default_model(),
            default_temperature=self._coerce_float(os.getenv("OPENAI_TEMPERATURE"), get_env_default_temperature()),
            default_max_output_tokens=self._coerce_int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS"), get_env_default_max_output_tokens()),
            timeout_seconds=self._coerce_int(os.getenv("OPENAI_TIMEOUT_SECONDS"), 60),
            app_env=os.getenv("APP_ENV", "development").strip() or "development",
        )

    def _build_metadata(self, prompt_payload: dict[str, Any]) -> dict[str, Any]:
        """Combine prompt metadata into a safe request metadata payload."""

        metadata = dict(prompt_payload.get("metadata") or prompt_payload.get("orchestration_metadata") or {})
        metadata.setdefault("brand", prompt_payload.get("brand", ""))
        metadata.setdefault("content_type", prompt_payload.get("content_type", ""))
        metadata.setdefault("context_used", prompt_payload.get("context_used", []))
        metadata.setdefault("platform_rules", prompt_payload.get("platform_rules", []))
        metadata.setdefault("provider", "openai")
        if not metadata.get("model"):
            metadata["model"] = self.config.default_model
        if metadata.get("temperature") is None:
            metadata["temperature"] = self.config.default_temperature
        if metadata.get("max_output_tokens") is None:
            metadata["max_output_tokens"] = self.config.default_max_output_tokens
        metadata.setdefault("estimated_tokens", None)
        metadata.setdefault("cost_estimate", None)
        return metadata

    def _resolve_model_name(self, value: Any) -> str:
        """Resolve a valid model name with fallback to the configured default."""

        candidate = str(value or "").strip()
        if candidate and is_supported_model(candidate, provider="openai"):
            return candidate
        if is_supported_model(self.config.default_model, provider="openai"):
            return self.config.default_model
        return get_env_default_model()

    def _extract_response_text(self, response: Any) -> str:
        """Extract text from a Responses API response."""

        text = getattr(response, "output_text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        output = getattr(response, "output", None)
        if isinstance(output, list):
            chunks: list[str] = []
            for item in output:
                chunk = self._walk_response_item(item)
                if chunk:
                    chunks.append(chunk)
            if chunks:
                return "\n".join(chunks).strip()

        fallback = getattr(response, "content", None)
        if isinstance(fallback, str):
            return fallback.strip()
        return ""

    def _walk_response_item(self, item: Any) -> str:
        """Walk a nested Responses API item to find textual content."""

        if isinstance(item, dict):
            if item.get("type") == "message":
                return self._walk_response_item(item.get("content"))
            if "text" in item and isinstance(item["text"], str):
                return item["text"].strip()
            if "content" in item:
                return self._walk_response_item(item["content"])
            return ""

        if isinstance(item, list):
            parts = [self._walk_response_item(part) for part in item]
            return "\n".join(part for part in parts if part).strip()

        text = getattr(item, "text", None)
        if isinstance(text, str) and text.strip():
            return text.strip()

        content = getattr(item, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            return self._walk_response_item(content)
        return ""

    def _serialize_response(self, response: Any) -> dict[str, Any]:
        """Serialize the raw SDK response when possible."""

        if hasattr(response, "model_dump"):
            try:
                return response.model_dump()
            except Exception:
                pass
        if hasattr(response, "to_dict"):
            try:
                return response.to_dict()
            except Exception:
                pass
        return {"repr": repr(response)}

    def _sanitize_metadata(self, metadata: dict[str, Any]) -> dict[str, str]:
        """Reduce metadata to a Responses API-safe payload.

        The Responses API accepts a maximum of 16 metadata properties. This
        helper preserves priority fields first, converts values to strings,
        truncates long values, removes nested payloads, and drops any overflow.
        """

        safe_source = dict(metadata or {})
        sanitized: dict[str, str] = {}
        dropped_keys: list[str] = []

        for key in PRIORITY_METADATA_FIELDS:
            if key not in safe_source or safe_source[key] is None:
                continue
            sanitized[key] = self._sanitize_metadata_value(safe_source[key])

        for key, value in safe_source.items():
            if key in sanitized or key in PRIORITY_METADATA_FIELDS:
                continue
            if len(sanitized) >= MAX_OPENAI_METADATA_KEYS:
                dropped_keys.append(str(key))
                continue
            sanitized[str(key)] = self._sanitize_metadata_value(value)

        if len(sanitized) > MAX_OPENAI_METADATA_KEYS:
            overflow_keys = list(sanitized.keys())[MAX_OPENAI_METADATA_KEYS:]
            for key in overflow_keys:
                dropped_keys.append(key)
                sanitized.pop(key, None)

        if dropped_keys:
            log_warning(
                self.logger,
                f"OpenAI metadata trimmed to {MAX_OPENAI_METADATA_KEYS} keys; dropped={dropped_keys}",
            )

        return sanitized

    def _sanitize_metadata_value(self, value: Any) -> str:
        """Convert metadata values into safe flat strings."""

        if value is None:
            return ""
        if isinstance(value, bool):
            text = "true" if value else "false"
        elif isinstance(value, (str, int, float)):
            text = str(value)
        else:
            text = self._stringify_complex_value(value)

        text = " ".join(text.split())
        if len(text) > MAX_METADATA_VALUE_LENGTH:
            text = text[: MAX_METADATA_VALUE_LENGTH - 3].rstrip() + "..."
        return text

    def _stringify_complex_value(self, value: Any) -> str:
        """Stringify non-primitive metadata without leaking nested payloads."""

        if isinstance(value, dict):
            return json.dumps({str(k): self._simplify_scalar(v) for k, v in value.items() if self._is_simple_value(v)}, ensure_ascii=False)
        if isinstance(value, (list, tuple, set)):
            simplified = [self._simplify_scalar(item) for item in value if self._is_simple_value(item)]
            return json.dumps(simplified, ensure_ascii=False)
        return str(value)

    def _simplify_scalar(self, value: Any) -> Any:
        """Return a scalar-friendly representation for JSON conversion."""

        if isinstance(value, bool):
            return value
        if isinstance(value, (str, int, float)):
            return value
        return str(value)

    def _is_simple_value(self, value: Any) -> bool:
        """Return whether a value is a supported primitive-like metadata item."""

        return isinstance(value, (str, int, float, bool))

    def _coerce_float(self, value: Any, fallback: float) -> float:
        """Convert a value to float safely."""

        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback

    def _coerce_int(self, value: Any, fallback: int) -> int:
        """Convert a value to int safely."""

        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    def _sanitize_error(self, message: str) -> str:
        """Remove secrets or noisy internals from error messages."""

        if not message:
            return "OpenAI generation failed."
        return message.replace(os.getenv("OPENAI_API_KEY", ""), "[redacted]")

    def _failure(self, model_name: str, metadata: dict[str, Any], message: str) -> dict[str, Any]:
        """Return a structured failure payload."""

        return OpenAIGenerationResult(
            success=False,
            provider="openai",
            model=model_name,
            content="",
            raw_response=None,
            metadata={
                **metadata,
                "provider": "openai",
                "model": model_name,
                "estimated_tokens": metadata.get("estimated_tokens", None),
                "cost_estimate": metadata.get("cost_estimate", None),
            },
            error=message,
        ).to_dict()


if __name__ == "__main__":
    logger = get_logger("openai_client_demo")
    client = OpenAIClient(logger=logger)
    print("Configuration valid:", client.validate_configuration())
    print("Health check:", client.health_check())
    sample_payload = {
        "system_prompt": "You are a concise marketing assistant.",
        "user_prompt": "Write a short Instagram caption about a bright Mallorca apartment.",
        "content_type": "instagram_post",
        "brand": "sample_brand",
        "metadata": {
            "provider": "openai",
            "model": client.config.default_model,
        },
    }
    print(json.dumps(client.generate_text(sample_payload), indent=2, ensure_ascii=False)[:4000])
