from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.storage.storage_manager import StorageManager


def test_api_storage_records_and_latest(tmp_path, auth_services) -> None:
    storage = StorageManager(storage_root=tmp_path)
    saved = storage.save_report(
        {
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "campaign_type": "property_launch",
            "metadata": {"brand": "wenzel_partner", "workflow_id": "wf-123"},
            "consolidated_report": {"title": "Stored Report", "status": "completed"},
        },
        overwrite=True,
        write_markdown=False,
    )
    app = create_app(services={"storage": storage, **auth_services})
    client = TestClient(app)

    register = client.post(
        "/auth/register",
        json={"email": "storage@example.com", "password": "Password123", "display_name": "Storage User"},
    )
    token = register.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    list_response = client.get("/storage/records", params={"record_type": "report"})
    item_response = client.get(f"/storage/records/report/{saved['record_id']}")
    latest_response = client.get("/reports/latest", headers=headers)

    assert list_response.status_code == 200
    assert list_response.json()["success"] is True
    assert list_response.json()["data"]["count"] >= 1
    assert item_response.status_code == 200
    assert item_response.json()["success"] is True
    assert item_response.json()["data"]["record_id"] == saved["record_id"]
    assert latest_response.status_code == 200
    assert latest_response.json()["success"] is True
