"""API router aggregation."""

from __future__ import annotations

from fastapi import APIRouter, HTMLResponse, Request

from src.api.api_config import ApiConfig
from src.api.health import build_health_payload
from src.api.routes_assets import router as assets_router
from src.api.routes_campaigns import router as campaigns_router
from src.api.routes_config import router as config_router
from src.api.routes_generate import router as generate_router
from src.api.routes_analytics import router as analytics_router
from src.api.routes_reports import router as reports_router
from src.api.routes_storage import router as storage_router
from src.api.routes_workflows import router as workflows_router
from src.api.api_result import build_api_response


router = APIRouter()
router.include_router(generate_router)
router.include_router(analytics_router)
router.include_router(workflows_router)
router.include_router(campaigns_router)
router.include_router(assets_router)
router.include_router(reports_router)
router.include_router(storage_router)
router.include_router(config_router)


@router.get("/health", summary="Health check", description="Return a lightweight service health summary.")
def health(request: Request) -> dict[str, object]:
    return build_api_response(success=True, data=build_health_payload(), metadata={"route": "health"})


def build_docs_html(app) -> str:
    routes = getattr(app, "routes", [])
    rows = []
    for route in routes:
        rows.append(f"<tr><td>{route.method}</td><td><code>{route.path}</code></td><td>{route.summary or route.name}</td></tr>")
    config = ApiConfig()
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{config.api_title}</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 0; background: #f5f4f0; color: #1f2328; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 40px 24px 72px; }}
    .hero {{ display: grid; gap: 12px; padding: 24px; background: white; border: 1px solid #ddd7cc; border-radius: 20px; box-shadow: 0 12px 40px rgba(23, 29, 41, 0.06); }}
    h1 {{ margin: 0; font-size: 2rem; }}
    p {{ margin: 0; color: #5a6472; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 24px; background: white; border-radius: 16px; overflow: hidden; }}
    th, td {{ padding: 12px 14px; border-bottom: 1px solid #e7e2d8; text-align: left; }}
    th {{ background: #faf7f1; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.08em; }}
    code {{ background: #f2efe8; padding: 2px 6px; border-radius: 8px; }}
  </style>
</head>
<body>
<main>
  <section class=\"hero\">
    <h1>{config.api_title}</h1>
    <p>Local API docs for the AI Marketing Content System.</p>
    <p>Version: {config.api_version} | Environment: {config.environment}</p>
  </section>
  <table>
    <thead><tr><th>Method</th><th>Path</th><th>Summary</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</main>
</body>
</html>"""
