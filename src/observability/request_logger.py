"""FastAPI-compatible request logging helpers for safe observability."""

from __future__ import annotations

from functools import wraps
from time import perf_counter
from typing import Any, Callable
import uuid

from .logger import emit_event
from .metrics_registry import get_metrics_registry
from .error_tracker import get_error_tracker
from .observability_context import build_context, clear_context


class RequestLoggingMiddleware:
    """Request logging middleware compatible with FastAPI's middleware stack."""

    def __init__(self, app, logger: Any | None = None) -> None:
        self.app = app
        self.logger = logger

    def wrap(self, handler: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(handler)
        def wrapped(method: str, path: str, **kwargs: Any) -> Any:
            registry = get_metrics_registry()
            headers = dict(kwargs.get("headers") or {})
            request_id = headers.get("x-request-id") or headers.get("X-Request-ID") or uuid.uuid4().hex
            headers["X-Request-ID"] = request_id
            kwargs["headers"] = headers
            build_context(
                request_context={
                    "method": method,
                    "path": path,
                    "request_id": request_id,
                },
                metadata={
                    "headers_present": bool(headers),
                },
            )
            started = perf_counter()
            status_code = 500
            try:
                response = handler(method, path, **kwargs)
                status_code = getattr(response, "status_code", 500)
                if hasattr(response, "headers"):
                    response.headers["X-Request-ID"] = request_id
                return response
            except Exception as exc:
                get_error_tracker().record_error(
                    error_type=type(exc).__name__,
                    module="api",
                    message=str(exc),
                    request_id=request_id,
                    severity="error",
                )
                raise
            finally:
                duration_ms = (perf_counter() - started) * 1000.0
                path_value = path.rstrip("/") or "/"
                registry.increment_counter("total_requests")
                registry.increment_counter("requests_by_path", labels={"path": path_value})
                registry.increment_counter("requests_by_status", labels={"status": str(status_code)})
                registry.record_duration("request_duration_ms", duration_ms)
                if status_code >= 400:
                    registry.increment_counter("error_count")
                emit_event(
                    "http_request",
                    module="request_logger",
                    request_id=request_id,
                    duration_ms=duration_ms,
                    metadata={
                        "method": method,
                        "path": path_value,
                        "status_code": status_code,
                    },
                )
                clear_context()

        return wrapped


def install_request_logging(app, logger: Any | None = None) -> None:
    if hasattr(app, "add_middleware"):
        app.add_middleware(RequestLoggingMiddleware, logger=logger)
        return
    middleware = RequestLoggingMiddleware(app, logger=logger)
    if hasattr(app, "handle_request"):
        original = app.handle_request

        @wraps(original)
        def wrapped_handle_request(method: str, path: str, *, json_body: Any = None, headers: dict[str, str] | None = None, query: dict[str, Any] | None = None):
            wrapped = middleware.wrap(
                lambda inner_method, inner_path, **kwargs: original(
                    inner_method,
                    inner_path,
                    json_body=kwargs.get("json_body"),
                    headers=kwargs.get("headers"),
                    query=kwargs.get("query"),
                )
            )
            return wrapped(method, path, json_body=json_body, headers=headers, query=query)

        app.handle_request = wrapped_handle_request
