from __future__ import annotations

from src.observability.runtime_monitor import build_runtime_diagnostics


def test_runtime_monitor_is_safe() -> None:
    diagnostics = build_runtime_diagnostics()

    assert diagnostics["python_version"]
    assert diagnostics["app_env"]
    assert isinstance(diagnostics["storage_root_exists"], bool)
    assert isinstance(diagnostics["storage_root_writable"], bool)
    assert "OPENAI_API_KEY" not in str(diagnostics)
