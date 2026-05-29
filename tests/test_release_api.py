from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.api.api_config import ApiConfig
from src.api.main import create_app
from src.api import routes_release


class _FakeReleaseManager:
    def build_release_summary(self, app=None):
        return {
            "mvp_ready": True,
            "release_ready": True,
            "production_ready": True,
            "version": "1.0.0",
            "release_score": 98,
            "overall_score": 98,
            "release_status": "ready",
            "recommendations": [],
            "maturity": {"maturity_score": 96, "maturity_level": "production_ready"},
            "governance": {"governance_status": "approved"},
            "certification": {"mvp_certified": True, "production_ready": True, "certification_status": "approved", "version": "1.0.0"},
            "release_health": {"overall_health": "healthy", "health_score": 97},
            "release_checklist": {"total_checks": 150, "passed": 150, "failed": 0, "warnings": 0, "items": []},
            "release_audit": {"audit_passed": True, "modules": {}},
            "executive_summary": "# summary",
            "release_artifacts": "# artifacts",
            "final_mvp_declaration": {"mvp_complete": True, "version": "1.0.0", "release_status": "approved", "maturity_level": "production_ready", "production_ready": True, "certified": True},
            "mvp_acceptance": {"mvp_ready": True, "release_ready": True, "version": "1.0.0", "acceptance_score": 98, "status": "approved", "certification": {}, "declaration": {}},
        }

    def generate_release_report(self, summary=None):
        return {"generated": True, "path": "docs/MVP_READINESS_REPORT.md", "content": "# MVP Readiness Report"}


def _admin_user():
    return {"success": True, "user": {"user_id": "u1", "role": "admin", "status": "active"}}


def test_release_api_endpoints_return_api_response(monkeypatch) -> None:
    app = create_app(ApiConfig())
    monkeypatch.setattr(routes_release, "get_current_user_result", lambda request: _admin_user())
    monkeypatch.setattr(routes_release, "_get_release_manager", lambda request: _FakeReleaseManager())
    client = TestClient(app)

    for path in ["/release/status", "/release/certification", "/release/maturity", "/release/governance", "/release/executive-summary", "/release/readiness", "/release/health", "/release/checklist", "/release/report", "/release/score"]:
        response = client.get(path)
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert "data" in payload


def test_release_api_blocks_non_manager_users(monkeypatch) -> None:
    app = create_app(ApiConfig())
    monkeypatch.setattr(routes_release, "get_current_user_result", lambda request: {"success": True, "user": {"user_id": "u2", "role": "viewer", "status": "active"}})
    client = TestClient(app)
    response = client.get("/release/status")
    assert response.status_code == 403
