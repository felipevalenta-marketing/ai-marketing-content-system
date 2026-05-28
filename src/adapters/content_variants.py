"""Deterministic variant builders for platform adaptation."""

from __future__ import annotations

from typing import Any


def build_content_variants(base_content: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Create deterministic content variants without inventing new facts."""

    return {
        "primary_variant": dict(base_content),
        "short_variant": _shorten_variant(base_content),
        "premium_variant": _make_premium_variant(base_content),
        "relocation_variant": _make_relocation_variant(base_content),
        "investment_variant": _make_investment_variant(base_content),
    }


def _shorten_variant(base_content: dict[str, Any]) -> dict[str, Any]:
    variant = dict(base_content)
    for key in ("caption", "post", "body", "long_description"):
        if isinstance(variant.get(key), str):
            variant[key] = _truncate_sentences(variant[key], max_sentences=2)
    return variant


def _make_premium_variant(base_content: dict[str, Any]) -> dict[str, Any]:
    variant = dict(base_content)
    for key in ("caption", "post", "body", "long_description", "short_description"):
        if isinstance(variant.get(key), str) and variant[key]:
            variant[key] = variant[key]
    return variant


def _make_relocation_variant(base_content: dict[str, Any]) -> dict[str, Any]:
    variant = dict(base_content)
    for key in ("caption", "post", "body", "long_description"):
        if isinstance(variant.get(key), str):
            variant[key] = _append_soft_relocation_angle(variant[key])
    return variant


def _make_investment_variant(base_content: dict[str, Any]) -> dict[str, Any]:
    variant = dict(base_content)
    for key in ("caption", "post", "body", "long_description"):
        if isinstance(variant.get(key), str):
            variant[key] = _append_investment_caution(variant[key])
    return variant


def _truncate_sentences(text: str, max_sentences: int = 2) -> str:
    if not text:
        return text
    parts = [part.strip() for part in text.split(".") if part.strip()]
    if len(parts) <= max_sentences:
        return text.strip()
    return ". ".join(parts[:max_sentences]).strip() + "."


def _append_soft_relocation_angle(text: str) -> str:
    if not text or "relocation" in text.lower() or "move" in text.lower():
        return text.strip()
    suffix = " It also supports a calm, practical relocation perspective."
    return text.strip() + suffix


def _append_investment_caution(text: str) -> str:
    if not text or "investment" in text.lower():
        return text.strip()
    suffix = " Consider this as a lifestyle-led property opportunity, subject to verification."
    return text.strip() + suffix
