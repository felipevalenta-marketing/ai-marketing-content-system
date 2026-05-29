from __future__ import annotations

from src.configuration.module_registry import build_module_registry


def test_module_registry_lists_core_modules() -> None:
    modules = build_module_registry()
    module_names = {str(module.get("module")) for module in modules}

    assert {"authentication", "users", "rbac", "brands", "workflows", "analytics", "reporting", "storage", "campaigns", "assets"}.issubset(module_names)

