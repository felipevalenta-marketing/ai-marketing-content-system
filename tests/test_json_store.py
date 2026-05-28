"""Tests for safe JSON persistence helpers."""

from __future__ import annotations

from pathlib import Path

from src.storage.json_store import json_exists, read_json, write_json


def test_write_and_read_json_round_trip(tmp_path: Path):
    path = tmp_path / "sample.json"
    result = write_json(path, {"hello": "world"})
    assert result["success"] is True
    assert json_exists(path) is True

    loaded = read_json(path)
    assert loaded["success"] is True
    assert loaded["record"]["hello"] == "world"


def test_write_json_respects_overwrite_flag(tmp_path: Path):
    path = tmp_path / "sample.json"
    assert write_json(path, {"first": True})["success"] is True
    second = write_json(path, {"second": True}, overwrite=False)
    assert second["success"] is False
