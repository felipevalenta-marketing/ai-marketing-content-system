"""FastAPI-style application entrypoint for the local API demo."""

from __future__ import annotations

from dataclasses import replace
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
from src.rbac.rbac_manager import RBACManager
from src.pipeline.content_generation_pipeline import ContentGenerationPipeline
from src.pipeline.pipeline_config import PipelineConfig
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
        "logger": logger,
        "pipeline_config": pipeline_config,
    }


def create_app(config: ApiConfig | None = None, services: dict[str, Any] | None = None) -> FastAPI:
    api_config = config or ApiConfig()
    app = FastAPI(title=api_config.api_title, version=api_config.api_version)
    app.state.config = api_config
    app.state.api_debug = api_config.api_debug
    app.state.services = services or build_services(api_config)
    app.state.cors_origins = list(api_config.cors_origins)
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

        uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
        return 0
    except Exception:
        print("uvicorn is not installed in this environment.")
        print("Run the API after installing dependencies:")
        print("  uvicorn src.api.main:app --reload")
        print(f"Frontend: {Path('frontend').resolve() / 'index.html'}")
        print(f"Config: {build_safe_config_summary()}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
