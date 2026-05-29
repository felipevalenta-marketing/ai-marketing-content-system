from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.observability.request_logger import install_request_logging


def test_request_logger_omits_authorization_header() -> None:
    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict[str, str]:
        return {"ok": "yes"}

    install_request_logging(app)
    client = TestClient(app)

    logger = logging.getLogger("amcs.observability")
    records: list[logging.LogRecord] = []

    class CaptureHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # type: ignore[override]
            records.append(record)

    handler = CaptureHandler()
    logger.addHandler(handler)
    try:
        response = client.get("/ping", headers={"Authorization": "Bearer secret-token"})
    finally:
        logger.removeHandler(handler)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    rendered = "\n".join(record.getMessage() for record in records)
    assert "secret-token" not in rendered
    assert "Authorization" not in rendered
