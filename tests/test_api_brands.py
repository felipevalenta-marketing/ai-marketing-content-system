from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.brands.brand_manager import BrandManager


def _make_brand(root: Path, brand_id: str, *, active: bool = True, config: str | None = None) -> None:
    brand = root / brand_id
    brand.mkdir(parents=True, exist_ok=True)
    for name in ("audience.md", "positioning.md", "tone_of_voice.md", "content_rules.md"):
        (brand / name).write_text(f"{name} for {brand_id}", encoding="utf-8")
    if config is not None:
        (brand / "brand.json").write_text(config, encoding="utf-8")


def test_api_brands_endpoints_surface_health_and_defaults(tmp_path: Path, auth_services) -> None:
    brand_root = tmp_path / "brands"
    brand_root.mkdir()
    _make_brand(
        brand_root,
        "wenzel_partner",
        config='{"brand_id":"wenzel_partner","display_name":"Wenzel & Partner","default_platform":"instagram","default_content_type":"instagram_post","default_campaign_type":"property_launch","default_language":"en","active":true}',
    )
    _make_brand(brand_root, "inactive_brand", config='{"brand_id":"inactive_brand","active":false}')

    app = create_app(services={"brands": BrandManager(brand_root=str(brand_root)), **auth_services})
    client = TestClient(app)

    register = client.post("/auth/register", json={"email": "brands@example.com", "password": "Password123", "display_name": "Brand User"})
    token = register.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    listing = client.get("/brands", headers=headers)
    active_listing = client.get("/brands", params={"active_only": True}, headers=headers)
    profile = client.get("/brands/wenzel_partner", headers=headers)
    health = client.get("/brands/wenzel_partner/health", headers=headers)
    defaults = client.get("/brands/wenzel_partner/defaults", headers=headers)
    validation = client.get("/brands/wenzel_partner/validate", headers=headers)

    assert listing.status_code == 200
    assert listing.json()["success"] is True
    assert listing.json()["data"]["count"] == 2
    assert active_listing.json()["data"]["count"] == 1
    assert profile.json()["data"]["status"] == "active"
    assert profile.json()["data"]["health_score"] >= 80
    assert health.json()["data"]["health_status"] == "healthy"
    assert defaults.json()["data"]["defaults"]["default_platform"] == "instagram"
    assert validation.json()["data"]["valid"] is True
    assert "sk-" not in str(profile.json())
