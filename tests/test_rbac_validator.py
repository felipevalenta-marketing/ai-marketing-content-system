from __future__ import annotations

from src.rbac.rbac_validator import validate_rbac_configuration, validate_role_assignment


def test_rbac_validator_and_self_escalation() -> None:
    config = validate_rbac_configuration()
    assert config["valid"] is True

    viewer = {"user_id": "usr_1", "role": "viewer", "permissions": []}
    target = validate_role_assignment(viewer, "admin", "usr_1", "usr_1")
    assert target["valid"] is False
    assert any("self role assignment" in error.lower() for error in target["errors"])

