"""Security middleware helpers."""

from __future__ import annotations

from functools import wraps
from hashlib import sha256
from time import perf_counter
from typing import Any, Callable
import uuid

from fastapi import JSONResponse

from src.api.api_result import build_api_response
from src.auth.current_user import extract_bearer_token, get_current_user_result
from src.observability.error_tracker import get_error_tracker
from src.observability.log_sanitizer import redact_log_payload
from src.observability.logger import emit_event
from src.observability.metrics_registry import get_metrics_registry
from src.security.input_sanitizer import sanitize_request_params
from src.security.input_sanitizer import sanitize_input
from src.security.output_sanitizer import sanitize_output
from src.security.rate_limiter import get_rate_limiter
from src.security.security_config import build_security_configuration
from src.security.security_context import build_context as build_security_context
from src.security.security_headers import build_security_headers
from src.security.security_events import record_security_event


class SecurityMiddleware:
    def __init__(self, app, logger: Any | None = None) -> None:
        self.app = app
        self.logger = logger

    def wrap(self, handler: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(handler)
        def wrapped(method: str, path: str, **kwargs: Any) -> Any:
            config = build_security_configuration(self.app)
            headers = dict(kwargs.get("headers") or {})
            query = dict(kwargs.get("query") or {})
            body = kwargs.get("json_body")
            request_id = headers.get("x-request-id") or headers.get("X-Request-ID") or uuid.uuid4().hex
            headers["X-Request-ID"] = request_id
            token = extract_bearer_token(type("RequestLike", (), {"headers": headers})())
            current_user = get_current_user_result(type("RequestLike", (), {"app": self.app, "headers": headers})())
            user = current_user.get("user", {}) if isinstance(current_user, dict) and current_user.get("success") and isinstance(current_user.get("user"), dict) else {}
            role = str(user.get("role", "anonymous")).lower() if user else "anonymous"
            identity = self._identity(token=token, user=user, headers=headers)
            path_value = str(path or "/")
            if config.get("input_sanitization_enabled", True):
                sanitized_query = sanitize_request_params(query)
                if sanitized_query.get("errors"):
                    return self._blocked_response("Invalid request parameters.", 400, request_id, headers, query, body, user, path_value)
                query = sanitized_query.get("value", query)
                if isinstance(body, (dict, list, str)):
                    body_check = sanitize_input(body)
                    if body_check.get("errors"):
                        return self._blocked_response("Invalid request body.", 400, request_id, headers, query, body, user, path_value)
            try:
                body_size_kb = len(str(body).encode("utf-8")) / 1024.0 if body is not None else 0.0
                query_size_kb = len(str(query).encode("utf-8")) / 1024.0 if query is not None else 0.0
            except Exception:
                body_size_kb = 0.0
                query_size_kb = 0.0
            if (body_size_kb + query_size_kb) > float(config.get("request_size_limit_kb", 256)):
                return self._blocked_response("Request payload is too large.", 413, request_id, headers, query, body, user, path_value, warnings=["Request size limit exceeded."])
            if config.get("rate_limiting_enabled", True):
                normalized_path = path_value.strip().lower().strip("/")
                skip_rate_limit = normalized_path in {"health", "health/live", "health/ready"}
                allowed = {"allowed": True} if skip_rate_limit else get_rate_limiter().allow_request(identity, role, config=None)
                if not allowed.get("allowed", True):
                    record_security_event(event_type="rate_limit_exceeded", severity="warning", module="security_middleware", message="Rate limit exceeded.", metadata={"path": path_value, "role": role, "request_id": request_id})
                    return self._blocked_response("Rate limit exceeded.", 429, request_id, headers, query, body, user, path_value, warnings=["Rate limit exceeded."])
            build_security_context(
                request_context={"method": method, "path": path_value, "request_id": request_id},
                auth_context={"user_id": user.get("user_id", ""), "role": role},
                rbac_context={"permissions": user.get("permissions", [])},
                organization_context={"organization_id": user.get("active_organization_id", ""), "team_id": user.get("active_team_id", "")},
                metadata={"headers_present": bool(headers)},
            )
            started = perf_counter()
            status_code = 500
            try:
                response = handler(method, path, json_body=body, headers=headers, query=query)
                status_code = getattr(response, "status_code", 500)
                if hasattr(response, "headers"):
                    response.headers.update(build_security_headers(app=self.app))
                    response.headers["X-Request-ID"] = request_id
                if config.get("output_sanitization_enabled", True):
                    response = self._sanitize_response(response)
                return response
            except Exception as exc:
                get_error_tracker().record_error(error_type=type(exc).__name__, module="security", message=str(exc), request_id=request_id, severity="critical")
                raise
            finally:
                duration_ms = (perf_counter() - started) * 1000.0
                registry = get_metrics_registry()
                registry.increment_counter("total_requests")
                registry.increment_counter("requests_by_path", labels={"path": path_value})
                registry.increment_counter("requests_by_status", labels={"status": str(status_code)})
                registry.record_duration("request_duration_ms", duration_ms)
                if status_code >= 400:
                    registry.increment_counter("error_count")
                emit_event(
                    "security_request",
                    module="security_middleware",
                    request_id=request_id,
                    user_id=str(user.get("user_id", "")),
                    organization_id=str(user.get("active_organization_id", "")),
                    workflow_id="",
                    duration_ms=duration_ms,
                    metadata=redact_log_payload({"method": method, "path": path_value, "status_code": status_code, "role": role}),
                )

        return wrapped

    def _identity(self, *, token: str, user: dict[str, Any], headers: dict[str, str]) -> str:
        if user.get("user_id"):
            return f"user:{user.get('user_id')}"
        if token:
            return f"token:{sha256(token.encode('utf-8')).hexdigest()[:16]}"
        forwarded = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For") or "anonymous"
        return f"anon:{forwarded}"

    def _sanitize_response(self, response: Any) -> Any:
        if hasattr(response, "content") and isinstance(response.content, (dict, list)):
            response.content = sanitize_output(response.content)
            try:
                import json

                response.text = json.dumps(response.content, ensure_ascii=False, default=str)
            except Exception:
                pass
        return response

    def _blocked_response(
        self,
        message: str,
        status_code: int,
        request_id: str,
        headers: dict[str, str],
        query: dict[str, Any],
        body: Any,
        user: dict[str, Any],
        path_value: str,
        *,
        warnings: list[str] | None = None,
    ) -> JSONResponse:
        payload = build_api_response(success=False, data=None, warnings=warnings or [], errors=[message], metadata={"route": "security", "request_id": request_id})
        response = JSONResponse(payload, status_code=status_code)
        response.headers.update(build_security_headers(app=self.app))
        response.headers["X-Request-ID"] = request_id
        get_error_tracker().record_error(error_type="SecurityViolation", module="security", message=message, request_id=request_id, severity="warning" if status_code < 500 else "critical")
        record_security_event(event_type="security_violation", severity="warning" if status_code < 500 else "critical", module="security_middleware", message=message, metadata={"path": path_value, "status_code": status_code, "request_id": request_id})
        return response


def install_security_middleware(app, logger: Any | None = None) -> None:
    middleware = SecurityMiddleware(app, logger=logger)
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
        return
    if hasattr(app, "add_middleware"):
        app.add_middleware(SecurityMiddleware, logger=logger)
