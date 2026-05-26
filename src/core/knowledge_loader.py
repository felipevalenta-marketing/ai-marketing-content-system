"""Recursive markdown knowledge loader for brand intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json

from src.core.context_registry import ContextRegistry
from src.utils.file_utils import (
    MarkdownFileRecord,
    group_by_key,
    normalize_key,
    normalize_markdown_content,
    read_markdown_file,
    recursive_markdown_files,
    validate_path,
)
from src.utils.logger import get_logger, log_error, log_load, log_scan, log_warning


KNOWLEDGE_ROOT_NAME = "knowledge_base"
BRAND_CONFIG_NAME = "brand_config"


@dataclass
class KnowledgeFile:
    """A loaded markdown file and its metadata."""

    key: str
    filename: str
    path: str
    relative_path: str
    category_path: tuple[str, ...]
    category: str
    semantic_role: str
    priority: str
    usage_tags: list[str] = field(default_factory=list)
    raw_content: str = ""
    normalized_content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrandKnowledge:
    """Structured knowledge bundle for a single brand."""

    brand: str
    brand_root: str
    brand_config: dict[str, Any] = field(default_factory=dict)
    knowledge_base: dict[str, Any] = field(default_factory=dict)
    raw_content: dict[str, str] = field(default_factory=dict)
    normalized_content: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    files: list[KnowledgeFile] = field(default_factory=list)
    detected_categories: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class KnowledgeLoader:
    """Load markdown-based brand intelligence into structured context."""

    def __init__(self, brands_root: str | Path | None = None, logger=None) -> None:
        self.brands_root = Path(brands_root or "brands").resolve()
        self.logger = logger or get_logger(self.__class__.__name__)
        self.registry = ContextRegistry()

    def detect_brands(self) -> list[str]:
        """Detect available brand folders dynamically."""

        if not self.brands_root.exists():
            log_warning(self.logger, f"Brands root does not exist: {self.brands_root}")
            return []

        brands = sorted(
            path.name
            for path in self.brands_root.iterdir()
            if path.is_dir() and (path / BRAND_CONFIG_NAME).exists() and (path / KNOWLEDGE_ROOT_NAME).exists()
        )
        log_scan(self.logger, f"Detected brands: {brands}")
        return brands

    def load_brand(self, brand_name: str) -> BrandKnowledge:
        """Load all markdown knowledge for a specific brand."""

        normalized_brand = normalize_key(brand_name)
        brand_root = self.brands_root / normalized_brand
        if not brand_root.exists():
            warning = f"Brand folder not found: {brand_root}"
            log_error(self.logger, warning)
            return BrandKnowledge(brand=normalized_brand, brand_root=str(brand_root), warnings=[warning])

        brand_config_root = brand_root / BRAND_CONFIG_NAME
        knowledge_root = brand_root / KNOWLEDGE_ROOT_NAME

        bundle = BrandKnowledge(brand=normalized_brand, brand_root=str(brand_root))
        bundle.brand_config = self._load_section(brand_config_root, section_name=BRAND_CONFIG_NAME, bundle=bundle)
        bundle.knowledge_base = self._load_section(knowledge_root, section_name=KNOWLEDGE_ROOT_NAME, bundle=bundle)
        bundle.detected_categories = self._collect_categories(bundle)
        self._log_summary(bundle)
        return bundle

    def _load_section(self, section_root: Path, section_name: str, bundle: BrandKnowledge) -> dict[str, Any]:
        """Load a section folder into a nested dictionary."""

        if not section_root.exists():
            warning = f"Missing folder: {section_root}"
            bundle.warnings.append(warning)
            log_warning(self.logger, warning)
            return {}

        records = recursive_markdown_files(section_root)
        log_scan(self.logger, f"Scanning {section_name} at {section_root} -> {len(records)} markdown files")

        grouped = group_by_key(records)
        for key, items in grouped.items():
            if len(items) > 1:
                warning = f"Duplicate filename key '{key}' in {section_root}"
                bundle.warnings.append(warning)
                log_warning(self.logger, warning)

        section_data: dict[str, Any] = {}
        for record in records:
            record_content = self._read_content(record, bundle)
            self._insert_record(section_data, record, record_content)
            bundle.files.append(
                KnowledgeFile(
                    key=record.filename_key,
                    filename=Path(record.relative_path).name,
                    path=str(record.path),
                    relative_path=record.relative_path,
                    category_path=record.category_path,
                    category=record.category_path[0] if record.category_path else section_name,
                    semantic_role=self._resolve_role(record),
                    priority=self._resolve_priority(record),
                    usage_tags=self._resolve_usage_tags(record),
                    raw_content=record_content["raw"],
                    normalized_content=record_content["normalized"],
                    metadata=record_content["metadata"],
                )
            )

        return section_data

    def _read_content(self, record: MarkdownFileRecord, bundle: BrandKnowledge) -> dict[str, Any]:
        """Read file content with error handling."""

        try:
            raw_content = read_markdown_file(record.path)
            normalized_content = normalize_markdown_content(raw_content)
            if not raw_content.strip():
                warning = f"Empty markdown file: {record.path}"
                bundle.warnings.append(warning)
                log_warning(self.logger, warning)
            log_load(self.logger, f"Loaded {record.relative_path}")
            bundle.raw_content[record.relative_path] = raw_content
            bundle.normalized_content[record.relative_path] = normalized_content
            metadata = self._build_metadata(record, raw_content, normalized_content)
            bundle.metadata[record.relative_path] = metadata
            return {
                "raw": raw_content,
                "normalized": normalized_content,
                "metadata": metadata,
            }
        except Exception as exc:  # noqa: BLE001
            warning = f"Failed to load {record.path}: {exc}"
            bundle.warnings.append(warning)
            log_error(self.logger, warning)
            return {"raw": "", "normalized": "", "metadata": self._build_metadata(record, "", "")}

    def _insert_record(self, tree: dict[str, Any], record: MarkdownFileRecord, content: dict[str, Any]) -> None:
        """Insert a markdown file into a nested dictionary."""

        current = tree
        for part in record.category_path:
            current = current.setdefault(part, {})

        filename_key = record.filename_key
        existing = current.get(filename_key)
        payload = {
            "content": content["raw"],
            "normalized_content": content["normalized"],
            "metadata": content["metadata"],
            "path": str(record.path),
            "relative_path": record.relative_path,
            "category_path": record.category_path,
        }
        if existing is None:
            current[filename_key] = payload
        elif isinstance(existing, list):
            existing.append(payload)
        else:
            current[filename_key] = [existing, payload]

    def _collect_categories(self, bundle: BrandKnowledge) -> list[str]:
        """Collect high-level categories discovered during loading."""

        categories = set(bundle.brand_config.keys()) | set(bundle.knowledge_base.keys())
        categories.discard("readme")
        return sorted(categories)

    def _resolve_role(self, record: MarkdownFileRecord) -> str:
        """Resolve the semantic role for a file."""

        return self.registry.resolve(record.relative_path).role

    def _resolve_priority(self, record: MarkdownFileRecord) -> str:
        """Resolve the semantic priority for a file."""

        return self.registry.resolve(record.relative_path).priority

    def _resolve_usage_tags(self, record: MarkdownFileRecord) -> list[str]:
        """Resolve the usage tags for a file."""

        return self.registry.resolve(record.relative_path).usage

    def _build_metadata(self, record: MarkdownFileRecord, raw_content: str, normalized_content: str) -> dict[str, Any]:
        """Build the metadata payload stored with each loaded markdown file."""

        registry_entry = self.registry.resolve(record.relative_path)
        category = record.category_path[0] if record.category_path else ""
        return {
            "filename": Path(record.relative_path).name,
            "relative_path": record.relative_path,
            "category": category,
            "semantic_role": registry_entry.role,
            "priority": registry_entry.priority,
            "usage_tags": registry_entry.usage,
            "raw_content": raw_content,
            "normalized_content": normalized_content,
        }

    def _log_summary(self, bundle: BrandKnowledge) -> None:
        """Log a concise ingestion summary for developer ergonomics."""

        self.logger.info(
            "[summary] brand=%s files=%s categories=%s warnings=%s",
            bundle.brand,
            len(bundle.files),
            ", ".join(bundle.detected_categories),
            len(bundle.warnings),
        )


def load_brand_knowledge(brand_name: str, brands_root: str | Path | None = None) -> BrandKnowledge:
    """Convenience helper for loading a brand knowledge bundle."""

    loader = KnowledgeLoader(brands_root=brands_root)
    return loader.load_brand(brand_name)


if __name__ == "__main__":
    logger = get_logger("knowledge_loader_demo")
    loader = KnowledgeLoader(logger=logger)

    brands = loader.detect_brands()
    print("Detected brands:", brands)

    if "wenzel_partner" in brands:
        bundle = loader.load_brand("wenzel_partner")
        print("Detected categories:", bundle.detected_categories)
        print("Context registry snapshot:", loader.registry.describe(["brand_config/tone.md", "brand_story/buyer_psychology.md"]))
        print("Structured output preview:")
        preview = {
            "brand": bundle.brand,
            "brand_config": bundle.brand_config,
            "knowledge_base": bundle.knowledge_base,
            "metadata": list(bundle.metadata.values())[:3],
        }
        print(json.dumps(preview, indent=2, ensure_ascii=False)[:6000])
    else:
        print("Wenzel brand folder not found.")
