"""Multi-brand management orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.brands.brand_defaults import get_brand_defaults
from src.brands.brand_profile import build_brand_profile
from src.brands.brand_registry import build_brand_registry, discover_brands, is_valid_brand_id, normalize_brand_id
from src.brands.brand_result import build_failure_result, build_not_found_result, build_success_result, build_validation_result
from src.brands.brand_validator import validate_brand
from src.brands.brand_health import build_brand_health
from src.reporting.report_metrics import safe_bool, safe_dict, safe_text, utc_now_iso
from src.utils.logger import get_logger


class BrandManager:
    def __init__(self, brand_root: str = "brands", default_brand: str = "wenzel_partner", require_valid_brand: bool = True, logger: Any | None = None) -> None:
        self.brand_root = str(brand_root)
        self.default_brand = normalize_brand_id(default_brand)
        self.require_valid_brand = bool(require_valid_brand)
        self.logger = logger or get_logger(self.__class__.__name__)

    def list_brands(self, active_only: bool = False, include_invalid: bool = False) -> dict[str, Any]:
        registry = build_brand_registry(self.brand_root)
        brands = self._filter_brands(registry.get("brands", []), active_only=active_only, include_invalid=include_invalid)
        return build_success_result(
            brands=brands,
            count=len(brands),
            root_path=registry.get("root_path", self.brand_root),
            updated_at=registry.get("updated_at", utc_now_iso()),
            metadata={"registry": registry},
        )

    def get_brand(self, brand_id: str) -> dict[str, Any]:
        raw_brand_id = str(brand_id or "").strip()
        if not raw_brand_id:
            return build_failure_result("Brand id is required.", brand_id=brand_id)
        if not is_valid_brand_id(raw_brand_id):
            return build_failure_result("Invalid brand id.", brand_id=brand_id)
        normalized = normalize_brand_id(raw_brand_id)
        if not self.is_brand_available(normalized):
            return build_not_found_result(normalized, brand_id=normalized)
        return self.build_brand_profile(normalized)

    def validate_brand(self, brand_id: str) -> dict[str, Any]:
        validation = validate_brand(brand_id, root_path=self.brand_root)
        return build_validation_result(validation, brand_id=normalize_brand_id(brand_id))

    def get_brand_defaults(self, brand_id: str) -> dict[str, Any]:
        raw_brand_id = str(brand_id or "").strip()
        if raw_brand_id and not is_valid_brand_id(raw_brand_id):
            return build_failure_result("Invalid brand id.", brand_id=brand_id, defaults={}, metadata={"brand_id": raw_brand_id})
        normalized = normalize_brand_id(raw_brand_id) or self.default_brand
        profile = build_brand_profile(normalized, root_path=self.brand_root)
        defaults = profile.get("defaults") if isinstance(profile, dict) and profile.get("defaults") else get_brand_defaults(normalized)
        return build_success_result(brand_id=normalized, defaults=defaults, metadata={"brand_id": normalized, "configuration_present": bool(profile.get("configuration_present")) if isinstance(profile, dict) else False})

    def get_brand_health(self, brand_id: str) -> dict[str, Any]:
        profile = self.build_brand_profile(brand_id)
        validation = safe_dict(profile.get("validation")) if isinstance(profile, dict) else {}
        health = build_brand_health(profile, validation)
        return build_success_result(brand_id=normalize_brand_id(brand_id), **health, metadata={"brand_id": normalize_brand_id(brand_id), "brand_profile": profile, "validation": validation})

    def resolve_brand_path(self, brand_id: str) -> dict[str, Any]:
        raw_brand_id = str(brand_id or "").strip()
        root = Path(self.brand_root).expanduser().resolve()
        if not raw_brand_id:
            return build_failure_result("Invalid brand id.", brand_id=brand_id, path="", root_path=str(root))
        if not is_valid_brand_id(raw_brand_id):
            return build_failure_result("Invalid brand id.", brand_id=brand_id, path="", root_path=str(root))
        normalized = normalize_brand_id(raw_brand_id)
        path = (root / normalized).resolve()
        if not str(path).startswith(str(root)):
            return build_failure_result("Resolved brand path is unsafe.", brand_id=normalized, path="", root_path=str(root))
        if not path.exists():
            return build_not_found_result(normalized, path=str(path), root_path=str(root))
        return build_success_result(brand_id=normalized, path=str(path), root_path=str(root))

    def build_brand_profile(self, brand_id: str) -> dict[str, Any]:
        raw_brand_id = str(brand_id or "").strip()
        if not raw_brand_id:
            return build_failure_result("Brand id is required.", brand_id=brand_id)
        if not is_valid_brand_id(raw_brand_id):
            return build_failure_result("Invalid brand id.", brand_id=brand_id)
        normalized = normalize_brand_id(raw_brand_id)
        profile = build_brand_profile(normalized, root_path=self.brand_root)
        validation = self.validate_brand(normalized)
        merged_defaults = profile.get("defaults", {})
        defaults_result = build_success_result(brand_id=normalized, defaults=merged_defaults, metadata={"brand_id": normalized})
        profile.update(
            {
                "defaults": merged_defaults,
                "validation": validation,
                "status": self._profile_status(profile, validation),
                "metadata": {
                    **profile.get("metadata", {}),
                    "brand_root": self.brand_root,
                    "default_brand": self.default_brand,
                    "require_valid_brand": self.require_valid_brand,
                },
            }
        )
        health = build_brand_health(profile, validation)
        profile["health_score"] = health.get("health_score", profile.get("health_score", 0))
        profile["health_status"] = health.get("health_status", profile.get("health_status", "critical"))
        profile["health"] = health
        profile["defaults_result"] = defaults_result
        profile["success"] = bool(profile.get("knowledge_path"))
        return profile

    def is_brand_available(self, brand_id: str) -> bool:
        raw_brand_id = str(brand_id or "").strip()
        if not raw_brand_id or not is_valid_brand_id(raw_brand_id):
            return False
        normalized = normalize_brand_id(raw_brand_id)
        return any(item.get("brand_id") == normalized for item in discover_brands(self.brand_root))

    def resolve_request_brand(self, brand_id: str | None) -> dict[str, Any]:
        raw_brand_id = str(brand_id or "").strip()
        if not raw_brand_id:
            normalized = self.default_brand
        elif not is_valid_brand_id(raw_brand_id):
            return build_failure_result(
                "Invalid brand id.",
                brand_id=brand_id,
                brand_profile={},
                brand_validation={"valid": False, "warnings": [], "errors": ["brand_id is not filesystem safe."], "checks": {}},
                defaults=get_brand_defaults(self.default_brand),
            )
        else:
            normalized = normalize_brand_id(raw_brand_id)
        profile = self.build_brand_profile(normalized) if self.is_brand_available(normalized) else {}
        validation = self.validate_brand(normalized) if normalized else {"valid": False, "warnings": [], "errors": ["Brand id is required."], "checks": {}}
        if self.require_valid_brand and not validation.get("valid", False):
            return build_failure_result(
                f"Invalid brand: {normalized}",
                brand_id=normalized,
                brand_profile=profile,
                brand_validation=validation,
                defaults=get_brand_defaults(normalized),
            )
        return build_success_result(
            brand_id=normalized,
            brand_profile=profile,
            brand_validation=validation,
            defaults=get_brand_defaults(normalized),
        )

    def filter_brands(self, brands: list[dict[str, Any]], active_only: bool = False, include_invalid: bool = False) -> list[dict[str, Any]]:
        return self._filter_brands(brands, active_only=active_only, include_invalid=include_invalid)

    def _profile_status(self, profile: dict[str, Any], validation: dict[str, Any]) -> str:
        if not profile or not profile.get("knowledge_path"):
            return "invalid"
        if not validation.get("valid", False):
            return "invalid"
        if profile.get("configuration_present") and safe_bool(safe_dict(profile.get("configuration")).get("active")) is False:
            return "inactive"
        if profile.get("missing_recommended_files") or profile.get("status") == "incomplete":
            return "incomplete"
        return "active"

    def _filter_brands(self, brands: list[dict[str, Any]], active_only: bool = False, include_invalid: bool = False) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []
        for brand in brands:
            if not isinstance(brand, dict):
                continue
            status = safe_text(brand.get("status"), limit=32).lower() or "unknown"
            if active_only and status != "active":
                continue
            if not include_invalid and status == "invalid":
                continue
            filtered.append(brand)
        return filtered


if __name__ == "__main__":
    manager = BrandManager()
    print("Brands:", manager.list_brands())
    print("Wenzel profile:", manager.get_brand("wenzel_partner"))
    print("Validation:", manager.validate_brand("wenzel_partner"))
    print("Missing brand:", manager.get_brand("missing_brand"))
    print("Unsafe brand:", manager.validate_brand("../bad"))
    print("Defaults:", manager.get_brand_defaults("wenzel_partner"))
