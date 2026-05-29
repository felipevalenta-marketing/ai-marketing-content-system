from __future__ import annotations

from pathlib import Path

from src.organizations.organization_registry import is_safe_path, is_valid_organization_id, normalize_organization_id


def test_organization_registry_normalizes_and_validates_ids() -> None:
    assert normalize_organization_id("Wenzel Partner") == "wenzel-partner"
    assert is_valid_organization_id("wenzel_partner") is True
    assert is_valid_organization_id("!!!") is False


def test_organization_registry_blocks_path_traversal(tmp_path: Path) -> None:
    root = tmp_path / "organizations"
    root.mkdir()
    safe_candidate = root / "acme"
    unsafe_candidate = tmp_path.parent / "outside"

    assert is_safe_path(root, safe_candidate) is True
    assert is_safe_path(root, unsafe_candidate) is False
