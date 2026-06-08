"""Validation rules for structured marketing outputs."""

from __future__ import annotations

from typing import Any

from src.output.output_contracts import get_output_contract, normalize_output_content_type
from src.utils.logger import get_logger, log_warning


class OutputValidator:
    """Validate formatted output against expected contracts."""

    def __init__(self, logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)

    def validate(self, output: dict[str, Any], content_type: str) -> dict[str, Any]:
        """Validate a formatted output and return structured diagnostics."""

        canonical_type = normalize_output_content_type(content_type)
        contract = get_output_contract(canonical_type)
        warnings: list[str] = []
        errors: list[str] = []

        errors.extend(self.validate_required_fields(output, contract.required_fields))
        errors.extend(self.validate_field_types(output, contract.field_types))
        warnings.extend(self.validate_empty_content(output, contract.required_fields))
        warnings.extend(self.validate_platform_expectations(output, canonical_type))

        if errors:
            log_warning(self.logger, "; ".join(errors))
        return {
            "valid": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "content_type": canonical_type,
            "required_fields": list(contract.required_fields),
        }

    def validate_required_fields(self, output: dict[str, Any], required_fields: tuple[str, ...]) -> list[str]:
        """Ensure required fields are present and non-empty."""

        errors: list[str] = []
        for field_name in required_fields:
            if field_name not in output:
                errors.append(f"Missing required field: {field_name}")
                continue
            if self._is_empty(output.get(field_name)):
                errors.append(f"Empty required field: {field_name}")
        return errors

    def validate_field_types(self, output: dict[str, Any], field_types: dict[str, tuple[str, ...]]) -> list[str]:
        """Validate field shapes against the expected type registry."""

        errors: list[str] = []
        for field_name, expected_types in field_types.items():
            value = output.get(field_name)
            if value is None:
                continue
            if "list" in expected_types and not isinstance(value, list):
                errors.append(f"Field '{field_name}' must be a list.")
            elif "str" in expected_types and not isinstance(value, str):
                errors.append(f"Field '{field_name}' must be a string.")
        return errors

    def validate_empty_content(self, output: dict[str, Any], required_fields: tuple[str, ...]) -> list[str]:
        """Warn when all meaningful content fields are empty."""

        non_empty = [field for field in required_fields if not self._is_empty(output.get(field))]
        if not non_empty:
            return ["Formatted output is empty."]
        return []

    def validate_platform_expectations(self, output: dict[str, Any], content_type: str) -> list[str]:
        """Validate content-type specific expectations."""

        warnings: list[str] = []
        if content_type in {"instagram_post", "instagram_reel"}:
            hashtags = output.get("hashtags", [])
            if not isinstance(hashtags, list):
                warnings.append("Hashtags should be a list for Instagram outputs.")
            elif not hashtags:
                warnings.append("Instagram output has no hashtags.")
            if self._is_empty(output.get("cta")):
                warnings.append("Instagram output is missing a CTA.")

        if content_type == "property_description":
            if self._is_empty(output.get("cta")):
                warnings.append("Property description is missing a CTA.")

        if content_type == "ad_copy" and self._is_empty(output.get("cta")):
            warnings.append("Ad copy is missing a CTA.")

        if content_type == "image_prompt":
            for field_name in ("image_prompt", "style", "camera", "lighting"):
                if self._is_empty(output.get(field_name)):
                    warnings.append(f"Image prompt is missing '{field_name}'.")

        if content_type == "video_prompt":
            for field_name in ("scene_description", "camera_motion", "mood", "sequence"):
                if self._is_empty(output.get(field_name)):
                    warnings.append(f"Video prompt is missing '{field_name}'.")

        if content_type == "video_script":
            for field_name in ("hook", "scene_1", "scene_2", "scene_3", "voiceover", "cta"):
                if self._is_empty(output.get(field_name)):
                    warnings.append(f"Video script is missing '{field_name}'.")
            if self._is_empty(output.get("scene_1")) and self._is_empty(output.get("script")):
                warnings.append("Video script is missing the main reel scene.")

        if content_type == "campaign_asset" and self._is_empty(output.get("cta")):
            warnings.append("Campaign asset is missing a CTA.")
        return warnings

    def _is_empty(self, value: Any) -> bool:
        """Return whether a value should be treated as empty."""

        if value is None:
            return True
        if isinstance(value, str):
            return not value.strip()
        if isinstance(value, list):
            return len(value) == 0
        if isinstance(value, dict):
            return len(value) == 0
        return False
