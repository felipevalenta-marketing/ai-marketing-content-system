"""Deterministic platform adaptation for structured outputs."""

from __future__ import annotations

from typing import Any

from src.adapters.adaptation_result import build_adaptation_failure, build_adaptation_success
from src.adapters.content_variants import build_content_variants
from src.adapters.platform_constraints import get_platform_constraints, list_supported_platforms
from src.adapters.platform_contracts import get_platform_contract, normalize_platform_name
from src.output.output_contracts import normalize_output_content_type
from src.utils.logger import get_logger, log_warning


class PlatformAdapter:
    """Repackage formatted outputs into platform-ready variants."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)

    def adapt(self, output: dict[str, Any], target_platforms: list[str]) -> dict[str, Any]:
        """Adapt one formatted output to multiple platforms."""

        source_content_type = normalize_output_content_type(str(output.get("content_type", "")))
        formatted = self._extract_formatted_output(output)
        metadata = dict(output.get("metadata") or {})

        if not formatted:
            return build_adaptation_failure(
                source_content_type=source_content_type,
                warnings=[],
                metadata=metadata,
                errors=["Missing formatted_output for platform adaptation."],
            )

        platform_variants: dict[str, dict[str, Any]] = {}
        warnings: list[str] = []
        errors: list[str] = []

        for platform in target_platforms:
            platform_name = normalize_platform_name(platform)
            if platform_name not in list_supported_platforms():
                warnings.append(f"Unsupported platform skipped: {platform}")
                continue
            adapter_method = getattr(self, f"adapt_to_{platform_name}", None)
            if adapter_method is None:
                warnings.append(f"No adapter available for platform: {platform_name}")
                continue
            variant_result = adapter_method(formatted)
            if variant_result.get("warnings"):
                warnings.extend(variant_result["warnings"])
            if variant_result.get("errors"):
                errors.extend(variant_result["errors"])
            platform_variants[platform_name] = variant_result

        metadata.update(
            {
                "source_content_type": source_content_type,
                "requested_platforms": target_platforms,
                "supported_platforms": list_supported_platforms(),
                "constraints": {
                    platform: get_platform_constraints(platform).to_dict() for platform in platform_variants.keys()
                },
            }
        )

        if not platform_variants:
            errors.append("No platform variants could be generated.")
            return build_adaptation_failure(source_content_type=source_content_type, warnings=warnings, metadata=metadata, errors=errors)

        return build_adaptation_success(
            source_content_type=source_content_type,
            platform_variants=platform_variants,
            warnings=warnings,
            metadata=metadata,
        )

    def adapt_to_instagram(self, output: dict[str, Any]) -> dict[str, Any]:
        """Adapt formatted output for Instagram."""

        contract = get_platform_contract("instagram")
        content = self._adapt_social_content(output, platform="instagram", contract=contract)
        return self._wrap_platform_result("instagram", content)

    def adapt_to_facebook(self, output: dict[str, Any]) -> dict[str, Any]:
        """Adapt formatted output for Facebook."""

        contract = get_platform_contract("facebook")
        content = self._adapt_social_content(output, platform="facebook", contract=contract)
        return self._wrap_platform_result("facebook", content)

    def adapt_to_linkedin(self, output: dict[str, Any]) -> dict[str, Any]:
        """Adapt formatted output for LinkedIn."""

        contract = get_platform_contract("linkedin")
        content = self._adapt_professional_content(output, contract=contract)
        return self._wrap_platform_result("linkedin", content)

    def adapt_to_email(self, output: dict[str, Any]) -> dict[str, Any]:
        """Adapt formatted output for email."""

        contract = get_platform_contract("email")
        content = self._adapt_email_content(output, contract=contract)
        return self._wrap_platform_result("email", content)

    def adapt_to_website_listing(self, output: dict[str, Any]) -> dict[str, Any]:
        """Adapt formatted output for a website listing."""

        contract = get_platform_contract("website_listing")
        content = self._adapt_website_content(output, contract=contract)
        return self._wrap_platform_result("website_listing", content)

    def _extract_formatted_output(self, output: dict[str, Any]) -> dict[str, Any]:
        """Get the structured formatted output from the pipeline payload."""

        formatted = output.get("formatted_output")
        if isinstance(formatted, dict):
            return dict(formatted)
        if isinstance(output, dict):
            return dict(output)
        return {}

    def _adapt_social_content(self, output: dict[str, Any], platform: str, contract: Any) -> dict[str, Any]:
        """Adapt content for social platforms without inventing facts."""

        cta = self._adapt_cta(output.get("cta"), platform)
        hashtags = self._adapt_hashtags(output.get("hashtags"), platform)
        if "hook" in output:
            hook = str(output.get("hook", "")).strip()
        else:
            hook = self._derive_hook(output)
        if "caption" in output:
            body = str(output.get("caption", "")).strip()
        else:
            body = self._join_source_text(output)
        if platform == "facebook":
            return {**contract.defaults, "post": body, "cta": cta, "hashtags": hashtags}
        return {**contract.defaults, "hook": hook, "caption": body, "cta": cta, "hashtags": hashtags}

    def _adapt_professional_content(self, output: dict[str, Any], contract: Any) -> dict[str, Any]:
        """Adapt content for LinkedIn without emotional exaggeration."""

        body = self._join_source_text(output)
        headline = self._derive_headline(output)
        hashtags = self._limit_hashtags(output.get("hashtags"), max_tags=3)
        cta = self._adapt_cta(output.get("cta"), "linkedin")
        return {**contract.defaults, "headline": headline, "body": body, "cta": cta, "hashtags": hashtags}

    def _adapt_email_content(self, output: dict[str, Any], contract: Any) -> dict[str, Any]:
        """Adapt content for email while keeping it clean and direct."""

        subject = self._derive_headline(output)
        body = self._join_source_text(output)
        preview_text = self._derive_preview_text(output)
        cta = self._adapt_cta(output.get("cta"), "email")
        return {**contract.defaults, "subject": subject, "preview_text": preview_text, "body": body, "cta": cta}

    def _adapt_website_content(self, output: dict[str, Any], contract: Any) -> dict[str, Any]:
        """Adapt content for website listing use."""

        title = str(output.get("title") or self._derive_headline(output)).strip()
        short_description = str(output.get("short_description") or self._derive_preview_text(output)).strip()
        long_description = str(output.get("long_description") or self._join_source_text(output)).strip()
        highlights = self._normalize_list(output.get("highlights"))
        cta = self._adapt_cta(output.get("cta"), "website_listing")
        return {**contract.defaults, "title": title, "short_description": short_description, "long_description": long_description, "highlights": highlights, "cta": cta}

    def _wrap_platform_result(self, platform: str, content: dict[str, Any]) -> dict[str, Any]:
        """Wrap a single platform adaptation result and attach deterministic variants."""

        variants = build_content_variants(content)
        return {
            "platform": platform,
            "content": content,
            "content_variants": variants,
            "constraints": get_platform_constraints(platform).to_dict(),
            "contract": get_platform_contract(platform).to_dict(),
            "warnings": [],
            "errors": [],
        }

    def _adapt_cta(self, cta: Any, platform: str) -> str:
        """Adjust CTA styling without changing its meaning."""

        text = str(cta or "").strip()
        if not text:
            return ""
        if platform == "linkedin":
            return text
        if platform == "email":
            return text
        if platform == "facebook":
            return text
        return text

    def _adapt_hashtags(self, hashtags: Any, platform: str) -> list[str]:
        """Adjust hashtag usage per platform."""

        tags = self._normalize_list(hashtags)
        if platform == "linkedin":
            return tags[:3]
        if platform == "facebook":
            return tags[:5]
        if platform == "email":
            return []
        if platform == "website_listing":
            return []
        return tags[:10]

    def _limit_hashtags(self, hashtags: Any, max_tags: int) -> list[str]:
        """Limit hashtags deterministically."""

        tags = self._normalize_list(hashtags)
        return tags[:max_tags]

    def _derive_headline(self, output: dict[str, Any]) -> str:
        """Derive a short headline from existing content."""

        for key in ("title", "hook", "headline", "subject", "campaign_name"):
            value = str(output.get(key, "")).strip()
            if value:
                return self._first_sentence(value)
        return self._first_sentence(self._join_source_text(output))

    def _derive_hook(self, output: dict[str, Any]) -> str:
        """Derive an Instagram-friendly hook from existing content."""

        candidate = str(output.get("hook") or output.get("title") or output.get("headline") or output.get("subject") or "").strip()
        if candidate:
            return self._truncate_words(candidate, 12)
        return self._truncate_words(self._join_source_text(output), 12)

    def _derive_preview_text(self, output: dict[str, Any]) -> str:
        """Derive a short preview text from existing content."""

        text = str(output.get("short_description") or output.get("caption") or output.get("body") or output.get("long_description") or "").strip()
        return self._truncate_words(text, 28)

    def _join_source_text(self, output: dict[str, Any]) -> str:
        """Join existing content fields into a readable paragraph."""

        parts: list[str] = []
        for key in ("caption", "body", "long_description", "short_description", "script", "scene_description", "main_message", "title"):
            value = output.get(key)
            if isinstance(value, str) and value.strip():
                parts.append(value.strip())
            elif isinstance(value, list):
                parts.extend([str(item).strip() for item in value if str(item).strip()])
        return "\n\n".join(dict.fromkeys(parts)).strip()

    def _normalize_list(self, value: Any) -> list[str]:
        """Convert a value into a stable string list."""

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",") if part.strip()]
            if parts:
                return parts
            return [value.strip()] if value.strip() else []
        if value is None:
            return []
        return [str(value).strip()] if str(value).strip() else []

    def _first_sentence(self, text: str) -> str:
        """Return the first sentence or a short fallback string."""

        text = text.strip()
        if not text:
            return ""
        for separator in (". ", "? ", "! "):
            if separator in text:
                return text.split(separator, 1)[0].strip()
        return self._truncate_words(text, 16)

    def _truncate_words(self, text: str, max_words: int) -> str:
        """Truncate text by word count."""

        words = text.split()
        if len(words) <= max_words:
            return text.strip()
        return " ".join(words[:max_words]).strip() + "..."


if __name__ == "__main__":
    logger = get_logger("platform_adapter_demo")
    adapter = PlatformAdapter(logger=logger)
    sample_output = {
        "content_type": "property_description",
        "formatted_output": {
            "title": "Rustic home near Sant Llorenc des Cardassar",
            "short_description": "A calm Mallorca property with modern comfort.",
            "long_description": "Rustic outside, modern inside, with practical access to services and nearby beaches.",
            "highlights": ["Quiet setting", "Modern interiors", "Near beaches"],
            "cta": "Request a viewing",
            "hashtags": ["#Mallorca", "#RealEstate"],
        },
        "metadata": {
            "brand": "sample_brand",
            "location": "sant_llorenc_des_cardassar",
            "audience": "relocation_clients",
        },
    }
    result = adapter.adapt(sample_output, ["instagram", "linkedin", "email", "website_listing"])
    print("Platform constraints:")
    print(get_platform_constraints("instagram").to_dict())
    print(get_platform_constraints("linkedin").to_dict())
    print(get_platform_constraints("email").to_dict())
    print("Adaptation result:")
    print(result)
