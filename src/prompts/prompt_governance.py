"""Prompt governance and guardrails for safe generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.prompts.prompt_contracts import build_output_instructions


@dataclass(frozen=True)
class PromptGovernance:
    """Reusable prompt guardrails and output formatting guidance."""

    rules: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_text(self) -> str:
        """Render governance instructions as a readable block."""

        lines = ["Prompt governance:"]
        lines.extend(f"- {rule}" for rule in self.rules)
        if self.warnings:
            lines.append("Warnings:")
            lines.extend(f"- {warning}" for warning in self.warnings)
        return "\n".join(lines)


DEFAULT_GOVERNANCE = PromptGovernance(
    rules=[
        "Do not hallucinate property facts, pricing, or availability.",
        "Do not invent investment returns or guarantees.",
        "Do not create exaggerated urgency.",
        "Keep tone consistent with the brand and role strategy.",
        "Do not claim unsupported neighborhood or market details.",
        "Separate instructions, context, and output formatting clearly.",
    ],
    warnings=[
        "If source context is missing, fall back to the safest generic phrasing.",
    ],
)


def build_prompt_governance(content_type: str) -> str:
    """Build governance guidance for a content type."""

    return f"{DEFAULT_GOVERNANCE.to_text()}\n\n{build_output_instructions(content_type)}"


def build_prompt_guardrails(content_type: str) -> list[str]:
    """Return a list of prompt guardrails for observability."""

    return list(DEFAULT_GOVERNANCE.rules) + [f"Output contract enforced for {content_type}."]


def governance_summary() -> dict[str, Any]:
    """Return governance metadata for prompt observability."""

    return {
        "rules": list(DEFAULT_GOVERNANCE.rules),
        "warnings": list(DEFAULT_GOVERNANCE.warnings),
    }
