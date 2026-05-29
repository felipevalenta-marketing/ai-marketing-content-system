"""Storage contracts for local persistence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.reports.markdown_utils import utc_now_iso


SUPPORTED_STORAGE_RECORD_TYPES = (
    "execution",
    "workflow",
    "workflow_state",
    "generation",
    "campaign",
    "asset",
    "report",
    "token_usage",
    "cost_usage",
    "creative_direction",
    "image_prompt",
    "video_script",
    "snapshot",
)


@dataclass(frozen=True)
class StorageRecordContract:
    record_id: str
    record_type: str
    created_at: str
    updated_at: str
    brand: str
    platform: str
    content_type: str
    campaign_type: str
    execution_id: str
    source_module: str
    payload: dict[str, Any]
    metadata: dict[str, Any]
    warnings: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "brand": self.brand,
            "platform": self.platform,
            "content_type": self.content_type,
            "campaign_type": self.campaign_type,
            "execution_id": self.execution_id,
            "source_module": self.source_module,
            "payload": self.payload,
            "metadata": self.metadata,
            "warnings": self.warnings,
            "errors": self.errors,
        }


@dataclass(frozen=True)
class StorageResultContract:
    success: bool
    record_type: str
    record_id: str
    path: str
    markdown_path: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "record_type": self.record_type,
            "record_id": self.record_id,
            "path": self.path,
            "markdown_path": self.markdown_path,
            "warnings": self.warnings,
            "errors": self.errors,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class StorageIndexContract:
    updated_at: str = field(default_factory=utc_now_iso)
    records: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"updated_at": self.updated_at, "records": self.records}


@dataclass(frozen=True)
class StoragePathContract:
    root: str
    record_type: str
    record_id: str
    path: str
    folder: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "record_type": self.record_type,
            "record_id": self.record_id,
            "path": self.path,
            "folder": self.folder,
        }


@dataclass(frozen=True)
class SnapshotContract:
    snapshot_id: str
    created_at: str
    records: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "created_at": self.created_at,
            "records": self.records,
            "metadata": self.metadata,
        }
