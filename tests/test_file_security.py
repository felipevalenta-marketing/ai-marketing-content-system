from __future__ import annotations

from src.security.file_security import is_allowed_extension, validate_file_name, validate_file_path


def test_file_security_validates_names_and_extensions() -> None:
    assert validate_file_name("report.md")["valid"] is True
    assert validate_file_path("data/report.md")["valid"] is True
    assert is_allowed_extension(".md") is True


def test_file_security_rejects_executables_and_traversal() -> None:
    assert validate_file_name("../../evil.exe")["valid"] is False
    assert validate_file_path("../evil.exe")["valid"] is False
    assert is_allowed_extension(".exe") is False

