from __future__ import annotations

from src.security.rbac_security import build_rbac_security_summary


def test_rbac_security_blocks_self_escalation() -> None:
    result = build_rbac_security_summary(
        actor={"user_id": "u1", "role": "viewer", "permissions": ["user:manage"]},
        target={"user_id": "u1", "role": "manager"},
    )
    assert result["allowed"] is False
    assert any("self-escalation" in error.lower() for error in result["errors"])


def test_rbac_security_blocks_cross_organization_escalation() -> None:
    result = build_rbac_security_summary(
        actor={"user_id": "u1", "role": "admin", "permissions": ["admin:all"]},
        target={"user_id": "u2", "role": "viewer"},
        organization_id="org-1",
        target_organization_id="org-2",
    )
    assert result["allowed"] is False
    assert any("organization boundary" in error.lower() for error in result["errors"])

