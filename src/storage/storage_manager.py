"""High-level local storage manager."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import copy

from src.reports.markdown_utils import safe_dict, safe_list, safe_text
from src.storage.json_store import read_json
from src.storage.markdown_store import render_record_markdown
from src.storage.storage_contracts import SUPPORTED_STORAGE_RECORD_TYPES
from src.storage.storage_index import StorageIndex
from src.storage.storage_paths import build_record_id, build_record_path, ensure_storage_dirs
from src.storage.storage_reader import StorageReader
from src.storage.storage_result import (
    build_failure_result,
    build_list_result,
    build_read_result,
    build_success_result,
    build_validation_failure_result,
)
from src.storage.storage_validator import StorageValidator
from src.storage.storage_writer import StorageWriter
from src.utils.logger import get_logger


PRUNED_STORAGE_KEYS = {
    "context",
    "context_summary",
    "combined_context",
    "storytelling_context",
    "prompt_payload",
    "prompt",
    "prompt_text",
    "input_prompt",
    "context_preview",
    "context_used",
    "payload_preview",
    "prompt_preview",
    "content_preview",
    "rendered_markdown",
    "rendered_text",
    "ai_response",
    "raw_response",
    "raw_provider_response",
    "openai_raw_response",
    "provider_response",
    "brand_context",
    "knowledge_base",
    "bundle",
    "raw_context",
    "context_bundle",
}


class StorageManager:
    """Coordinate safe local persistence across record types."""

    def __init__(self, storage_root: str | Path = "data", logger: Any | None = None) -> None:
        self.logger = logger or get_logger(self.__class__.__name__)
        self.storage_root = Path(storage_root)
        ensure_storage_dirs(self.storage_root)
        self.index = StorageIndex(storage_root=self.storage_root)
        self.validator = StorageValidator()
        self.writer = StorageWriter(storage_root=self.storage_root, index=self.index)
        self.reader = StorageReader(storage_root=self.storage_root, index=self.index)

    def save_record(self, record: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        """Validate and persist a storage record."""

        try:
            normalized = self._normalize_record(record)
        except Exception as exc:
            return build_validation_failure_result(
                errors=[str(exc)],
                warnings=[],
                record_type=safe_text(record.get("record_type") if isinstance(record, dict) else "", limit=80),
                record_id=safe_text(record.get("record_id") if isinstance(record, dict) else "", limit=160),
                metadata={"validation": {"valid": False, "errors": [str(exc)], "warnings": []}},
            )
        validation = self.validator.validate(normalized)
        if not validation["valid"]:
            return build_validation_failure_result(
                errors=validation.get("errors", []),
                warnings=validation.get("warnings", []),
                record_type=normalized.get("record_type", ""),
                record_id=normalized.get("record_id", ""),
                metadata={"validation": validation},
            )
        write_result = self.writer.write_record(normalized, overwrite=overwrite, write_markdown=write_markdown)
        if not write_result.get("success"):
            return build_failure_result(
                error="Failed to write storage record.",
                record_type=normalized.get("record_type", ""),
                record_id=normalized.get("record_id", ""),
                path=write_result.get("path", ""),
                warnings=list(write_result.get("warnings", [])),
                errors=list(write_result.get("errors", [])),
                metadata={"validation": validation},
            )
        return build_success_result(
            record_type=normalized.get("record_type", ""),
            record_id=normalized.get("record_id", ""),
            path=write_result.get("path", ""),
            markdown_path=write_result.get("markdown_path", ""),
            warnings=list(write_result.get("warnings", [])),
            errors=list(write_result.get("errors", [])),
            metadata={"validation": validation, "index_result": write_result.get("index_result", {})},
        )

    def load_record(self, record_type: str, record_id: str) -> dict[str, Any]:
        """Load a persisted record."""

        if safe_text(record_type, limit=80) not in SUPPORTED_STORAGE_RECORD_TYPES:
            return build_read_result(
                None,
                record_type=record_type,
                record_id=record_id,
                path="",
                warnings=[],
                errors=[f"Unsupported storage record_type: {record_type}"],
            )
        result = self.reader.read_record(record_type, record_id)
        return build_read_result(
            result.get("record"),
            record_type=record_type,
            record_id=record_id,
            path=result.get("path", ""),
            warnings=list(result.get("warnings", [])),
            errors=list(result.get("errors", [])),
        )

    def list_records(self, record_type: str | None = None) -> list[dict[str, Any]]:
        """List records from storage."""

        if record_type and safe_text(record_type, limit=80) not in SUPPORTED_STORAGE_RECORD_TYPES:
            return []
        return self.reader.list_records(record_type=record_type)

    def save_execution(self, result: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        return self.save_record(self._build_record(result, "execution"), overwrite=overwrite, write_markdown=write_markdown)

    def save_generation(self, result: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        return self.save_record(self._build_record(result, "generation"), overwrite=overwrite, write_markdown=write_markdown)

    def save_campaign(self, result: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        return self.save_record(self._build_record(result, "campaign"), overwrite=overwrite, write_markdown=write_markdown)

    def save_asset(self, result: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        return self.save_record(self._build_record(result, "asset"), overwrite=overwrite, write_markdown=write_markdown)

    def save_workflow(self, result: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        return self.save_record(self._build_record(result, "workflow"), overwrite=overwrite, write_markdown=write_markdown)

    def save_workflow_state(self, result: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        return self.save_record(self._build_record(result, "workflow_state"), overwrite=overwrite, write_markdown=write_markdown)

    def save_report(self, result: dict[str, Any], overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        return self.save_record(self._build_record(result, "report"), overwrite=overwrite, write_markdown=write_markdown)

    def save_tracking(self, result: dict[str, Any], tracking_type: str, overwrite: bool = False, write_markdown: bool = False) -> dict[str, Any]:
        return self.save_record(self._build_record(result, tracking_type), overwrite=overwrite, write_markdown=write_markdown)

    def build_snapshot(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Build a safe snapshot record from multiple stored records."""

        snapshot_id = build_record_id("snapshot", {"execution_id": "snapshot"})
        return {
            "snapshot_id": snapshot_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "records": [self._strip_sensitive(rec) for rec in records if isinstance(rec, dict)],
            "metadata": {"record_count": len(records)},
        }

    def _build_record(self, result: dict[str, Any], record_type: str) -> dict[str, Any]:
        metadata = safe_dict(result.get("metadata"))
        payload = self._build_payload(result)
        record = {
            "record_id": build_record_id(record_type, {
                "brand": result.get("brand") or metadata.get("brand", ""),
                "execution_id": metadata.get("execution", {}).get("started_at") or metadata.get("execution_id", ""),
                "campaign_id": result.get("campaign_type") or metadata.get("campaign_id", ""),
            }),
            "record_type": record_type,
            "created_at": self._timestamp(result, metadata),
            "updated_at": self._timestamp(result, metadata),
            "brand": safe_text(result.get("brand") or metadata.get("brand"), limit=120),
            "brand_id": safe_text(result.get("brand_id") or metadata.get("brand_id") or result.get("brand") or metadata.get("brand"), limit=120),
            "platform": safe_text(result.get("platform") or metadata.get("platform"), limit=120),
            "content_type": safe_text(result.get("content_type") or metadata.get("content_type"), limit=120),
            "campaign_type": safe_text(result.get("campaign_type") or metadata.get("campaign_type"), limit=120),
            "execution_id": safe_text(metadata.get("execution", {}).get("started_at") or metadata.get("execution_id", ""), limit=120),
            "source_module": self._source_module(record_type),
            "payload": payload,
            "metadata": self._sanitize_metadata(metadata),
            "warnings": safe_list(result.get("warnings")),
            "errors": safe_list(result.get("errors")),
        }
        if record_type == "report":
            record["payload"] = self._strip_sensitive(result.get("consolidated_report") or result.get("reporting") or payload)
        if record_type in {"token_usage", "cost_usage"}:
            record["payload"] = self._strip_sensitive(result)
        return record

    def _timestamp(self, result: dict[str, Any], metadata: dict[str, Any]) -> str:
        return safe_text(metadata.get("execution", {}).get("started_at") or metadata.get("created_at") or result.get("created_at") or datetime.now(timezone.utc).isoformat(), limit=80)

    def _source_module(self, record_type: str) -> str:
        mapping = {
            "execution": "pipeline",
            "workflow": "workflow",
            "workflow_state": "workflow",
            "generation": "pipeline",
            "campaign": "campaigns",
            "asset": "assets",
            "report": "reporting",
            "token_usage": "tracking",
            "cost_usage": "tracking",
            "creative_direction": "creative",
            "image_prompt": "media",
            "video_script": "media",
            "snapshot": "storage",
        }
        return mapping.get(record_type, "pipeline")

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(record, dict):
            raise TypeError("Record must be a dictionary.")
        normalized = copy.deepcopy(record or {})
        record_type = safe_text(normalized.get("record_type"), limit=80)
        if record_type not in SUPPORTED_STORAGE_RECORD_TYPES:
            raise ValueError(f"Unsupported storage record_type: {record_type}")
        normalized.setdefault("record_id", build_record_id(record_type, normalized.get("metadata", {})))
        normalized.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        normalized.setdefault("updated_at", normalized["created_at"])
        normalized.setdefault("brand", "")
        normalized.setdefault("brand_id", normalized.get("brand", ""))
        normalized.setdefault("platform", "")
        normalized.setdefault("content_type", "")
        normalized.setdefault("campaign_type", "")
        normalized.setdefault("execution_id", "")
        normalized.setdefault("source_module", "pipeline")
        normalized.setdefault("payload", {})
        normalized.setdefault("metadata", {})
        normalized.setdefault("warnings", [])
        normalized.setdefault("errors", [])
        return self._prune_storage_content(self._strip_sensitive(normalized))

    def _build_payload(self, result: dict[str, Any]) -> dict[str, Any]:
        payload = self._prune_storage_content(self._strip_sensitive(result))
        if isinstance(payload.get("metadata"), dict):
            payload["metadata"] = self._prune_metadata(payload["metadata"])
        return payload

    def _sanitize_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        sanitized = self._prune_metadata(self._strip_sensitive(metadata))
        if "reporting" in sanitized and isinstance(sanitized["reporting"], dict):
            sanitized["reporting"] = self._prune_storage_content(self._strip_sensitive(sanitized["reporting"]))
        return sanitized

    def _prune_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Remove verbose context blobs that do not belong in persisted storage."""

        pruned = self._prune_storage_content(self._strip_sensitive(metadata))
        if "routing" in pruned and isinstance(pruned["routing"], dict):
            routing = dict(pruned["routing"])
            routing.pop("metadata", None)
            pruned["routing"] = routing
        return pruned

    def _prune_storage_content(self, value: Any) -> Any:
        """Recursively remove raw context and prompt blobs from persisted content."""

        if isinstance(value, dict):
            pruned: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key).lower()
                if key_text in PRUNED_STORAGE_KEYS:
                    continue
                pruned[key] = self._prune_storage_content(item)
            return pruned
        if isinstance(value, list):
            return [self._prune_storage_content(item) for item in value]
        return value

    def _strip_sensitive(self, value: Any) -> Any:
        if isinstance(value, dict):
            sanitized: dict[str, Any] = {}
            for key, item in value.items():
                key_text = str(key).lower()
                if key_text in {"raw_response", "raw_provider_response", "provider_response", "openai_raw_response", "api_key", "openai_api_key", "secret", "password", "access_token", "refresh_token", "id_token", "auth_token", "bearer_token", "api_token", "session_token"}:
                    continue
                sanitized[key] = self._strip_sensitive(item)
            return sanitized
        if isinstance(value, list):
            return [self._strip_sensitive(item) for item in value]
        return value


if __name__ == "__main__":
    manager = StorageManager()
    sample = {
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "instagram_post",
        "campaign_type": "property_launch",
        "metadata": {"execution": {"started_at": datetime.now(timezone.utc).isoformat()}, "brand": "wenzel_partner"},
        "warnings": [],
        "errors": [],
        "token_usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    }
    saved = manager.save_generation(sample)
    print("Generation save:", saved)
    if saved.get("success"):
        loaded = manager.load_record("generation", saved["record_id"])
        print("Generation load:", loaded)
        print("Latest generation:", manager.list_records("generation")[:1])

    token_record = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
        "estimated": False,
        "source": "provider_usage",
        "execution_id": sample["metadata"]["execution"]["started_at"],
        "module": "instagram_post",
        "operation": "generation",
        "campaign_id": "property_launch",
        "asset_type": "instagram_post",
        "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
        "warnings": [],
        "errors": [],
    }
    print("Token tracking save:", manager.save_tracking(token_record, "token_usage"))

    cost_record = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "currency": "USD",
        "input_tokens": 10,
        "output_tokens": 5,
        "cached_input_tokens": 0,
        "total_tokens": 15,
        "input_cost": 0.0,
        "output_cost": 0.0,
        "cached_input_cost": 0.0,
        "total_cost": 0.0,
        "estimated_tokens": False,
        "estimated_cost": True,
        "pricing_found": False,
        "pricing_version": "local_default",
        "pricing_source": "configurable",
        "execution_id": sample["metadata"]["execution"]["started_at"],
        "module": "instagram_post",
        "operation": "generation",
        "campaign_id": "property_launch",
        "asset_type": "instagram_post",
        "metadata": {"brand": "wenzel_partner", "platform": "instagram"},
        "warnings": ["Pricing not found for provider/model."],
        "errors": [],
    }
    print("Cost tracking save:", manager.save_tracking(cost_record, "cost_usage"))

    snapshot = manager.build_snapshot([sample, token_record, cost_record])
    print("Snapshot:", snapshot)
    print("Markdown demo:", manager.save_record({
        "record_type": "generation",
        "record_id": "demo_markdown_generation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "brand": "wenzel_partner",
        "platform": "instagram",
        "content_type": "instagram_post",
        "campaign_type": "property_launch",
        "execution_id": sample["metadata"]["execution"]["started_at"],
        "source_module": "pipeline",
        "payload": sample,
        "metadata": {"brand": "wenzel_partner"},
        "warnings": [],
        "errors": [],
    }, write_markdown=True))
