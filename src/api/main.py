"""FastAPI-style application entrypoint for the local API demo."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import os

from fastapi import FastAPI, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.api.api_config import ApiConfig
from src.api.api_result import build_api_response
from src.api.routes import build_docs_html, router as api_router
from src.brands.brand_manager import BrandManager
from src.analytics.analytics_engine import AnalyticsEngine
from src.assets.asset_coordinator import AssetCoordinator
from src.campaigns.campaign_composer import CampaignComposer
from src.cli.cli_config import build_safe_config_summary
from src.auth.auth_manager import AuthManager, AuthService
from src.configuration.config_manager import ConfigManager
from src.organizations.brand_access_manager import BrandAccessManager
from src.organizations.membership_manager import MembershipManager
from src.organizations.organization_manager import OrganizationManager
from src.organizations.team_manager import TeamManager
from src.rbac.rbac_manager import RBACManager
from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig
from src.observability.log_config import configure_logging
from src.observability.request_logger import install_request_logging
from src.reporting.reporting_engine import ReportingEngine
from src.reports.markdown_generator import MarkdownReportGenerator
from src.storage.storage_manager import StorageManager
from src.users.user_manager import UserManager
from src.utils.logger import get_logger
from src.workflows.workflow_engine import WorkflowEngine


def build_services(config: ApiConfig | None = None) -> dict[str, Any]:
    api_config = config or ApiConfig()
    pipeline_config = PipelineConfig(
        enable_persistence=False,
        enable_reporting=True,
        enable_markdown_reports=True,
        enable_markdown_report_export=False,
        enable_api_layer=api_config.enable_api_layer,
        enable_frontend_demo=api_config.enable_frontend_demo,
        api_debug=api_config.api_debug,
    )
    configure_logging()
    logger = get_logger("api")
    storage_manager = StorageManager(storage_root=pipeline_config.storage_root, logger=logger)
    user_manager = UserManager(storage_path=pipeline_config.user_storage_path, logger=logger, default_role=pipeline_config.default_user_role, first_user_admin=pipeline_config.first_user_admin)
    auth_manager = AuthManager(
        user_manager=user_manager,
        jwt_secret=str(os.getenv("JWT_SECRET_KEY", "")).strip(),
        jwt_expiration_hours=pipeline_config.jwt_expiration_hours,
        logger=logger,
    )
    auth_service = AuthService(auth_manager)
    rbac_manager = RBACManager(user_manager=user_manager, logger=logger)
    brand_manager = BrandManager(
        brand_root=pipeline_config.brand_root,
        default_brand=pipeline_config.default_brand,
        require_valid_brand=pipeline_config.require_valid_brand,
        logger=logger,
    )
    reporting_engine = ReportingEngine(output_root=pipeline_config.report_output_root, markdown_output_root=pipeline_config.markdown_report_output_root, logger=logger)
    configuration_manager = ConfigManager(config_root="data/config", brand_manager=brand_manager)
    organization_manager = OrganizationManager(storage_root="data/organizations", users=user_manager, settings=configuration_manager, logger=logger)
    brand_access_manager = organization_manager.brand_access_manager or BrandAccessManager(storage_root="data/organizations", brand_manager=brand_manager, logger=logger)
    team_manager = organization_manager.membership_manager.team_manager if organization_manager.membership_manager else TeamManager(storage_root="data/organizations", organization_manager=organization_manager, logger=logger)
    membership_manager = organization_manager.membership_manager or MembershipManager(storage_root="data/organizations", users=user_manager, organization_manager=organization_manager, team_manager=team_manager, logger=logger)
    organization_manager.membership_manager = membership_manager
    organization_manager.brand_access_manager = brand_access_manager
    organization_manager.team_manager = team_manager
    membership_manager.organization_manager = organization_manager
    membership_manager.team_manager = team_manager
    team_manager.organization_manager = organization_manager
    pipeline = ContentGenerationPipeline(config=pipeline_config, logger=logger)
    workflow = WorkflowEngine(config=replace(pipeline_config, enable_persistence=False), pipeline=pipeline, storage_manager=storage_manager, reporting_engine=reporting_engine, logger=logger)
    analytics = AnalyticsEngine(storage_manager=storage_manager, reporting_engine=reporting_engine, logger=logger)
    return {
        "config": api_config,
        "pipeline": pipeline,
        "workflow": workflow,
        "analytics": analytics,
        "campaign": CampaignComposer(output_root=pipeline_config.campaign_output_root, logger=logger),
        "assets": AssetCoordinator(output_root=pipeline_config.asset_output_root, logger=logger),
        "markdown_report": MarkdownReportGenerator(output_root=pipeline_config.markdown_report_output_root, logger=logger),
        "storage": storage_manager,
        "users": user_manager,
        "auth": auth_service,
        "rbac": rbac_manager,
        "reporting": reporting_engine,
        "brands": brand_manager,
        "organizations": organization_manager,
        "teams": team_manager,
        "memberships": membership_manager,
        "brand_access": brand_access_manager,
        "configuration": configuration_manager,
        "logger": logger,
        "pipeline_config": pipeline_config,
    }


def create_app(config: ApiConfig | None = None, services: dict[str, Any] | None = None) -> FastAPI:
    api_config = config or ApiConfig()
    app = FastAPI(title=api_config.api_title, version=api_config.api_version)
    app.state.config = api_config
    app.state.api_debug = api_config.api_debug
    app.state.services = services or build_services(api_config)
    app.state.pipeline_config = app.state.services.get("pipeline_config") if isinstance(app.state.services, dict) else None
    app.state.started_at = getattr(app.state, "started_at", None) or datetime.now(timezone.utc).isoformat()
    app.state.cors_origins = list(api_config.cors_origins)
    pipeline_config = app.state.services.get("pipeline_config") if isinstance(app.state.services, dict) else None
    if getattr(pipeline_config, "enable_observability", True):
        if getattr(pipeline_config, "enable_request_logging", True):
            install_request_logging(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(api_config.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.include_router(api_router)

    @app.get("/openapi.json", summary="OpenAPI schema", description="Return the generated API schema.")
    def openapi(request: Any) -> dict[str, Any]:
        return app.openapi()

    @app.get("/docs", summary="API documentation", description="Return a minimal local documentation page.")
    def docs(request: Any) -> HTMLResponse:
        return HTMLResponse(build_docs_html(app))

    @app.get("/", summary="Root endpoint", description="Return a small landing response for the local API.")
    def root(request: Any) -> dict[str, Any]:
        return build_api_response(
            success=True,
            data={
                "service": api_config.service_name,
                "version": api_config.api_version,
                "environment": api_config.environment,
                "frontend_demo": api_config.enable_frontend_demo,
            },
            metadata={"route": "root"},
        )

    return app


app = create_app()


def main() -> int:
    api_config = ApiConfig()
    try:
        import uvicorn  # type: ignore

        uvicorn.run("src.api.main:app", host=api_config.api_host, port=api_config.api_port, reload=True)
        return 0
    except Exception:
        print("uvicorn is not installed in this environment.")
        print("Run the API after installing dependencies:")
        print(f"  uvicorn src.api.main:app --host {api_config.api_host} --port {api_config.api_port} --reload")
        print(f"Frontend: {Path('frontend').resolve() / 'index.html'}")
        print(f"Config: {build_safe_config_summary()}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
