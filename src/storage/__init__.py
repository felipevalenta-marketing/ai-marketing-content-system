"""Local storage and persistence utilities."""

from .json_store import json_exists, read_json, write_json
from .storage_index import StorageIndex
from .storage_manager import StorageManager
from .storage_paths import (
    build_record_id,
    build_record_path,
    ensure_storage_dirs,
    get_record_folder,
    sanitize_filename,
)
from .storage_reader import StorageReader
from .storage_result import (
    build_failure_result,
    build_list_result,
    build_read_result,
    build_success_result,
    build_validation_failure_result,
)
from .storage_validator import StorageValidator
from .storage_writer import StorageWriter

__all__ = [
    "StorageIndex",
    "StorageManager",
    "StorageReader",
    "StorageValidator",
    "StorageWriter",
    "build_failure_result",
    "build_list_result",
    "build_read_result",
    "build_success_result",
    "build_validation_failure_result",
    "build_record_id",
    "build_record_path",
    "ensure_storage_dirs",
    "get_record_folder",
    "json_exists",
    "read_json",
    "sanitize_filename",
    "write_json",
]
