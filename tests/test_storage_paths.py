"""Tests for safe storage path helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.storage.storage_paths import (
    build_record_id,
    build_record_path,
    ensure_storage_dirs,
    get_record_folder,
    sanitize_filename,
)


def test_sanitize_filename_removes_traversal_and_spaces():
    value = sanitize_filename("../My Dangerous File!!.json")
    assert value.startswith("my_dangerous_file")
    assert "/" not in value
    assert "\\" not in value


def test_build_record_id_includes_metadata_hints():
    record_id = build_record_id("generation", {"brand": "wenzel_partner", "execution_id": "exec-1", "campaign_id": "camp-1"})
    assert record_id.startswith("generation_wenzel_partner_exec-1_camp-1_")


def test_build_record_path_respects_custom_root(tmp_path: Path):
    record_path = build_record_path("generation", "demo-record", storage_root=tmp_path)
    assert str(record_path).startswith(str(tmp_path.resolve()))
    assert record_path.name == "demo-record.json"


def test_build_record_path_rejects_path_traversal(tmp_path: Path):
    with pytest.raises(ValueError):
        build_record_path("generation", "../../escape", storage_root=tmp_path)


def test_ensure_storage_dirs_creates_expected_folders(tmp_path: Path):
    ensure_storage_dirs(tmp_path)
    assert (tmp_path / "generations").exists()
    assert (tmp_path / "indexes").exists()
    assert (tmp_path / "tracking" / "tokens").exists()
    assert get_record_folder("report", storage_root=tmp_path) == tmp_path / "reports"
