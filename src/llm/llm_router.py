"""Provider and model routing for prompt-driven generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.llm.model_registry import ModelMetadata, resolve_model_for_content_type
from src.utils.file_utils import normalize_key
from src.utils.logger import get_logger, log_context


@dataclass(frozen=True)
class RoutingDecision:
    """Describe the selected provider and model."""

    provider: str
    model_name: str
    default_temperature: float
    max_output_tokens: int
    content_type: str
    route_reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def model(self) -> str:
        """Backward-compatible alias for the model name."""

        return self.model_name

    @property
    def temperature(self) -> float:
        """Backward-compatible alias for the model temperature."""

        return self.default_temperature

    def to_dict(self) -> dict[str, Any]:
        """Serialize the routing decision."""

        return {
            "provider": self.provider,
            "model": self.model_name,
            "model_name": self.model_name,
            "temperature": self.default_temperature,
            "default_temperature": self.default_temperature,
            "max_output_tokens": self.max_output_tokens,
            "content_type": self.content_type,
            "route_reason": self.route_reason,
            "metadata": self.metadata,
        }


class LLMRouter:
    """Resolve the best provider/model path for a content request."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)

    def route(
        self,
        content_type: str,
        provider: str | None = None,
        preferred_model: str | None = None,
        platform: str | None = None,
    ) -> RoutingDecision:
        """Route a content type to the appropriate provider and model."""

        content_key = normalize_key(content_type)
        selected_provider = normalize_key(provider or "openai") or "openai"
        metadata = resolve_model_for_content_type(content_key, provider=selected_provider, preferred_model=preferred_model)
        route_reason = self._build_route_reason(content_key, metadata, platform, preferred_model)
        decision = RoutingDecision(
            provider=selected_provider,
            model_name=metadata.model_name,
            default_temperature=metadata.default_temperature,
            max_output_tokens=metadata.max_output_tokens,
            content_type=content_key,
            route_reason=route_reason,
            metadata=metadata.to_dict(),
        )
        log_context(self.logger, f"Routed {content_key} to {decision.provider}/{decision.model_name}")
        return decision

    def _build_route_reason(
        self,
        content_key: str,
        metadata: ModelMetadata,
        platform: str | None,
        preferred_model: str | None,
    ) -> str:
        """Build a readable routing explanation."""

        pieces = [f"content_type={content_key}", f"model={metadata.model_name}"]
        if platform:
            pieces.append(f"platform={normalize_key(platform)}")
        if preferred_model:
            pieces.append(f"preferred_model={normalize_key(preferred_model)}")
        return ", ".join(pieces)
