from __future__ import annotations

from src.organizations.organization_validator import validate_organization


def test_organization_validator_accepts_valid_payload() -> None:
    result = validate_organization(
        {
            "organization_id": "org_demo",
            "name": "Demo Org",
            "slug": "demo-org",
            "status": "active",
            "settings": {},
        }
    )
    assert result["valid"] is True
    assert result["errors"] == []


def test_organization_validator_rejects_invalid_ids_and_flags_sensitive_content() -> None:
    result = validate_organization(
        {
            "organization_id": "",
            "name": "Demo Org",
            "slug": "demo-org",
            "status": "active",
            "metadata": {"OPENAI_API_KEY": "sk-test", "password_hash": "secret"},
        }
    )
    assert result["valid"] is False
    assert any("invalid organization_id" in error.lower() for error in result["errors"])
    assert result["warnings"]
