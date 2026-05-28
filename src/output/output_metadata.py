"""Safe metadata packaging for formatted and exported outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class OutputMetadata:
    """Export-safe metadata attached to structured outputs."""

    brand: str
    platform: str
    content_type: str
    objective: str = ""
    audience: str = ""
    location: str = ""
    property_type: str = ""
    model: str = ""
    provider: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validation_status: str = "unknown"
    export_paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize safe metadata for export and reporting."""

        return {
            "brand": self.brand,
            "platform": self.platform,
            "content_type": self.content_type,
            "objective": self.objective,
            "audience": self.audience,
            "location": self.location,
            "property_type": self.property_type,
            "model": self.model,
            "provider": self.provider,
            "generated_at": self.generated_at,
            "validation_status": self.validation_status,
            "export_paths": self.export_paths,
        }


def build_output_metadata(
    brand: str,
    platform: str,
    content_type: str,
    objective: str = "",
    audience: str = "",
    location: str = "",
    property_type: str = "",
    model: str = "",
    provider: str = "",
    validation_status: str = "unknown",
    export_paths: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build export-safe metadata for a generated output."""

    return OutputMetadata(
        brand=brand,
        platform=platform,
        content_type=content_type,
        objective=objective,
        audience=audience,
        location=location,
        property_type=property_type,
        model=model,
        provider=provider,
        validation_status=validation_status,
        export_paths=export_paths or {},
    ).to_dict()
