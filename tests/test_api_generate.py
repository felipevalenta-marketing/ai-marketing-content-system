from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.api.main import create_app
from src.pipeline.pipeline_config import PipelineConfig


class FakePipeline:
    def __init__(self) -> None:
        self.config = PipelineConfig()

    def generate(self, request: dict[str, object]) -> dict[str, object]:
        return {
            "success": True,
            "brand": request.get("brand", ""),
            "platform": request.get("platform", ""),
            "content_type": request.get("content_type", ""),
            "markdown_report": {"markdown": "# Generate Report"},
            "prompt_payload": {"system_prompt": "secret", "raw_response": {"secret": "hidden"}},
            "raw_response": {"secret": "hidden"},
            "token_usage": {"provider": "openai", "model": "gpt-4o-mini", "input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            "cost_usage": {"provider": "openai", "model": "gpt-4o-mini", "currency": "USD", "total_cost": 0.03},
            "warnings": ["safe warning"],
            "errors": [],
        }


def test_api_generate_returns_sanitized_response(auth_services) -> None:
    app = create_app(services={"pipeline": FakePipeline(), **auth_services})
    client = TestClient(app)

    register = client.post("/auth/register", json={"email": "generate@example.com", "password": "Password123", "display_name": "Generate User"})
    token = register.json()["data"]["access_token"]

    response = client.post(
        "/generate",
        json={
            "brand": "wenzel_partner",
            "platform": "instagram",
            "content_type": "instagram_post",
            "objective": "generate_leads",
            "report": True,
            "markdown": True,
            "dry_run": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["token_usage"]["total_tokens"] == 15
    assert "hidden" not in str(payload)
    assert "secret" not in str(payload)
