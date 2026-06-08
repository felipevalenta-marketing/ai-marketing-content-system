"""Minimal TestClient compatible with the local FastAPI shim."""

from __future__ import annotations

from typing import Any


class _TestClient:
    __test__ = False

    def __init__(self, app: Any) -> None:
        self.app = app

    def __enter__(self) -> "_TestClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def get(self, path: str, **kwargs: Any) -> Any:
        return self.app.handle_request("GET", path, json_body=kwargs.get("json"), headers=kwargs.get("headers"), query=kwargs.get("params"))

    def post(self, path: str, **kwargs: Any) -> Any:
        return self.app.handle_request("POST", path, json_body=kwargs.get("json"), headers=kwargs.get("headers"), query=kwargs.get("params"))

    def patch(self, path: str, **kwargs: Any) -> Any:
        return self.app.handle_request("PATCH", path, json_body=kwargs.get("json"), headers=kwargs.get("headers"), query=kwargs.get("params"))

    def options(self, path: str, **kwargs: Any) -> Any:
        return self.app.handle_request("OPTIONS", path, json_body=kwargs.get("json"), headers=kwargs.get("headers"), query=kwargs.get("params"))


TestClient = _TestClient
