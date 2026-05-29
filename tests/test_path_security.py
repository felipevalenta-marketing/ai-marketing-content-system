from __future__ import annotations

from src.security.path_security import is_safe_path, validate_path


def test_path_security_blocks_traversal() -> None:
    assert is_safe_path("../secrets.txt") is False
    assert is_safe_path("..\\secrets.txt") is False
    assert validate_path("../secrets.txt")["valid"] is False


def test_path_security_accepts_safe_relative_paths() -> None:
    assert is_safe_path("data/reports/latest.json") is True


def test_path_security_blocks_hidden_paths() -> None:
    assert is_safe_path(".env") is False
