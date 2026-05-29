"""Contracts for brand registry and profile payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.reporting.report_metrics import utc_now_iso


@dataclass(frozen=True)
class BrandProfileContract:
    success: bool
    brand_id: str
    display_name: str
    status: str
    knowledge_path: str
    available_files: list[str] = field(default_factory=list)
    missing_recommended_files: list[str] = field(default_factory=list)
    recommended_files: list[str] = field(default_factory=list)
    optional_files: list[str] = field(default_factory=list)
    defaults: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "brand_id": self.brand_id,
            "display_name": self.display_name,
            "status": self.status,
            "knowledge_path": self.knowledge_path,
            "available_files": self.available_files,
            "missing_recommended_files": self.missing_recommended_files,
            "recommended_files": self.recommended_files,
            "optional_files": self.optional_files,
            "defaults": self.defaults,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass(frozen=True)
class BrandRegistryContract:
    updated_at: str = field(default_factory=utc_now_iso)
    root_path: str = "brands"
    count: int = 0
    brands: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "updated_at": self.updated_at,
            "root_path": self.root_path,
            "count": self.count,
            "brands": self.brands,
        }


@dataclass(frozen=True)
class BrandValidationContract:
    valid: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "warnings": self.warnings,
            "errors": self.errors,
            "checks": self.checks,
        }


@dataclass(frozen=True)
class BrandDefaultsContract:
    brand_id: str
    defaults: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"brand_id": self.brand_id, "defaults": self.defaults, "metadata": self.metadata}


@dataclass(frozen=True)
class BrandApiResponseContract:
    success: bool
    data: Any | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }
