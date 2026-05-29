from __future__ import annotations

from src.configuration.feature_flags import FeatureFlagManager


def test_feature_flags_are_deterministic() -> None:
    manager = FeatureFlagManager({"analytics_dashboard": True, "workflow_execution": False})
    assert manager.is_enabled("analytics_dashboard") is True
    assert manager.is_disabled("workflow_execution") is True
    assert manager.is_enabled("missing") is False

