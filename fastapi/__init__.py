"""A lightweight FastAPI-compatible shim for local development and tests.

This project intentionally keeps the implementation small and dependency-free
so the API layer can be exercised without requiring the external FastAPI
package during local verification. The public surface mirrors the subset of
FastAPI used by the project:

- FastAPI
- APIRouter
- HTTPException
- Request
- Response / JSONResponse / HTMLResponse
- TestClient (via fastapi.testclient)
"""

from __future__ import annotations

from dataclasses import dataclass
from json import dumps, loads
from types import SimpleNamespace
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse
import inspect

try:  # pragma: no cover - optional import for validation handling
    from pydantic import ValidationError
except Exception:  # pragma: no cover - fallback when pydantic changes
    ValidationError = Exception  # type: ignore[assignment]


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: Any = "HTTP error") -> None:
        super().__init__(str(detail))
        self.status_code = int(status_code)
        self.detail = detail


class Response:
    media_type = "text/plain"

    def __init__(self, content: Any = "", status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        self.status_code = int(status_code)
        self.headers = dict(headers or {})
        self.content = content
        self.text = content if isinstance(content, str) else str(content)

    def json(self) -> Any:
        if isinstance(self.content, (dict, list)):
            return self.content
        try:
            return loads(self.text)
        except Exception:
            return self.content


class JSONResponse(Response):
    media_type = "application/json"

    def __init__(self, content: Any = None, status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        body = dumps(content, ensure_ascii=False, default=str)
        super().__init__(body, status_code=status_code, headers=headers)
        self.content = content
        self.text = body


class HTMLResponse(Response):
    media_type = "text/html"

    def __init__(self, content: Any = "", status_code: int = 200, headers: dict[str, str] | None = None) -> None:
        super().__init__(str(content), status_code=status_code, headers=headers)


@dataclass
class _Route:
    method: str
    path: str
    handler: Callable[..., Any]
    summary: str = ""
    description: str = ""
    request_model: Any | None = None
    response_model: Any | None = None
    name: str = ""


class Request:
    def __init__(self, app: "FastAPI", method: str, path: str, headers: dict[str, str] | None = None, query: dict[str, Any] | None = None, body: Any = None) -> None:
        self.app = app
        self.method = method
        self.url = SimpleNamespace(path=path)
        self.headers = dict(headers or {})
        self.query_params = dict(query or {})
        self._body = body

    async def json(self) -> Any:
        return self._body

    def json_sync(self) -> Any:
        return self._body


class APIRouter:
    def __init__(self, prefix: str = "", tags: list[str] | None = None) -> None:
        self.prefix = prefix.rstrip("/")
        self.tags = list(tags or [])
        self.routes: list[_Route] = []

    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        methods: list[str],
        *,
        summary: str = "",
        description: str = "",
        request_model: Any | None = None,
        response_model: Any | None = None,
        name: str = "",
    ) -> None:
        full_path = self._full_path(path)
        for method in methods:
            self.routes.append(
                _Route(
                    method=method.upper(),
                    path=full_path,
                    handler=endpoint,
                    summary=summary,
                    description=description,
                    request_model=request_model,
                    response_model=response_model,
                    name=name or getattr(endpoint, "__name__", "endpoint"),
                )
            )

    def get(self, path: str, *, summary: str = "", description: str = "", request_model: Any | None = None, response_model: Any | None = None, name: str = "") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(path, endpoint, ["GET"], summary=summary, description=description, request_model=request_model, response_model=response_model, name=name)
            return endpoint

        return decorator

    def post(self, path: str, *, summary: str = "", description: str = "", request_model: Any | None = None, response_model: Any | None = None, name: str = "") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(path, endpoint, ["POST"], summary=summary, description=description, request_model=request_model, response_model=response_model, name=name)
            return endpoint

        return decorator

    def patch(self, path: str, *, summary: str = "", description: str = "", request_model: Any | None = None, response_model: Any | None = None, name: str = "") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(endpoint: Callable[..., Any]) -> Callable[..., Any]:
            self.add_api_route(path, endpoint, ["PATCH"], summary=summary, description=description, request_model=request_model, response_model=response_model, name=name)
            return endpoint

        return decorator

    def include_router(self, router: "APIRouter") -> None:
        for route in router.routes:
            self.routes.append(route)

    def _full_path(self, path: str) -> str:
        base = self.prefix
        route = path if path.startswith("/") else f"/{path}"
        return f"{base}{route}" if base else route


class FastAPI(APIRouter):
    def __init__(self, title: str = "FastAPI App", version: str = "0.1.0", docs_url: str = "/docs", openapi_url: str = "/openapi.json") -> None:
        super().__init__()
        self.title = title
        self.version = version
        self.docs_url = docs_url
        self.openapi_url = openapi_url
        self.state = SimpleNamespace()
        self._middleware: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def add_middleware(self, *args: Any, **kwargs: Any) -> None:
        self._middleware.append((args, kwargs))

    def _build_request_handler(self) -> Callable[..., Response]:
        def base_handler(method: str, path: str, *, json_body: Any = None, headers: dict[str, str] | None = None, query: dict[str, Any] | None = None) -> Response:
            return self._handle_request_core(method, path, json_body=json_body, headers=headers, query=query)

        handler: Callable[..., Any] = base_handler
        for args, kwargs in reversed(self._middleware):
            middleware_cls = args[0] if args else None
            if middleware_cls is None or getattr(middleware_cls, "__name__", "") == "CORSMiddleware":
                continue
            middleware = middleware_cls(self, **kwargs) if callable(middleware_cls) else None
            if middleware is not None and hasattr(middleware, "wrap"):
                handler = middleware.wrap(handler)
        return handler

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Any], send: Callable[..., Any]) -> None:
        scope_type = scope.get("type")
        if scope_type == "lifespan":
            while True:
                message = await receive()
                if message.get("type") == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif message.get("type") == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
            return
        if scope_type != "http":
            await send({"type": "http.response.start", "status": 500, "headers": []})
            await send({"type": "http.response.body", "body": b"Unsupported scope"})
            return
        body = b""
        more_body = True
        while more_body:
            message = await receive()
            if message.get("type") != "http.request":
                break
            body += message.get("body", b"") or b""
            more_body = bool(message.get("more_body", False))
        raw_headers = scope.get("headers") or []
        headers: dict[str, str] = {}
        for key, value in raw_headers:
            if isinstance(key, bytes):
                key_text = key.decode("latin-1")
            else:
                key_text = str(key)
            if isinstance(value, bytes):
                value_text = value.decode("latin-1")
            else:
                value_text = str(value)
            headers[key_text] = value_text
        query_string = scope.get("query_string") or b""
        query: dict[str, Any] = {}
        if query_string:
            parsed_qs = parse_qs(query_string.decode("latin-1"))
            query = {key: values[0] if len(values) == 1 else values for key, values in parsed_qs.items()}
        json_body: Any = None
        if body:
            content_type = headers.get("content-type", "")
            try:
                if "application/json" in content_type:
                    json_body = loads(body.decode("utf-8"))
                else:
                    json_body = body.decode("utf-8")
            except Exception:
                json_body = body.decode("utf-8", errors="ignore")
        handler = self._build_request_handler()
        response = handler(scope.get("method", "GET"), scope.get("path", "/"), json_body=json_body, headers=headers, query=query)
        status_code = getattr(response, "status_code", 200)
        response_headers = [(key.encode("latin-1"), value.encode("latin-1")) for key, value in getattr(response, "headers", {}).items()]
        media_type = getattr(response, "media_type", "application/json")
        if not any(key.lower() == b"content-type" for key, _ in response_headers):
            response_headers.append((b"content-type", media_type.encode("latin-1")))
        await send({"type": "http.response.start", "status": status_code, "headers": response_headers})
        body_text = getattr(response, "text", "")
        if isinstance(body_text, bytes):
            body_bytes = body_text
        else:
            body_bytes = str(body_text).encode("utf-8")
        await send({"type": "http.response.body", "body": body_bytes})

    def openapi(self) -> dict[str, Any]:
        paths: dict[str, Any] = {}
        for route in self.routes:
            path_entry = paths.setdefault(route.path, {})
            method_entry = {
                "summary": route.summary or route.name,
                "description": route.description,
            }
            if route.request_model is not None:
                method_entry["requestModel"] = getattr(route.request_model, "__name__", str(route.request_model))
            if route.response_model is not None:
                method_entry["responseModel"] = getattr(route.response_model, "__name__", str(route.response_model))
            path_entry[route.method.lower()] = method_entry
        return {"openapi": "3.0.0", "info": {"title": self.title, "version": self.version}, "paths": paths}

    def _handle_request_core(self, method: str, path: str, *, json_body: Any = None, headers: dict[str, str] | None = None, query: dict[str, Any] | None = None) -> Response:
        cors_headers = self._cors_headers(headers)
        if method.upper() == "OPTIONS":
            return JSONResponse({}, status_code=200, headers=cors_headers)
        route, params = self._match_route(method, path)
        request = Request(self, method.upper(), path, headers=headers, query=query, body=json_body)
        try:
            body_arg = self._prepare_body(route, json_body)
            result = self._invoke(route.handler, request, params, body_arg)
            response = self._to_response(result)
            response.headers.update(cors_headers)
            return response
        except HTTPException as exc:
            return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=cors_headers)
        except Exception as exc:
            debug = bool(getattr(self.state, "api_debug", False))
            detail = {"detail": str(exc)} if debug else {"detail": "Internal server error"}
            return JSONResponse(detail, status_code=500, headers=cors_headers)

    def handle_request(self, method: str, path: str, *, json_body: Any = None, headers: dict[str, str] | None = None, query: dict[str, Any] | None = None) -> Response:
        handler = self._build_request_handler()
        return handler(method, path, json_body=json_body, headers=headers, query=query)

    def _match_route(self, method: str, path: str) -> tuple[_Route, dict[str, str]]:
        normalized_method = method.upper()
        normalized_path = path.rstrip("/") or "/"
        for route in self.routes:
            if route.method != normalized_method:
                continue
            params = self._match_path(route.path, normalized_path)
            if params is not None:
                return route, params
        raise HTTPException(404, f"Route not found: {method} {path}")

    def _match_path(self, template: str, path: str) -> dict[str, str] | None:
        template_parts = [part for part in template.strip("/").split("/") if part]
        path_parts = [part for part in path.strip("/").split("/") if part]
        if len(template_parts) != len(path_parts):
            return None
        params: dict[str, str] = {}
        for expected, actual in zip(template_parts, path_parts):
            if expected.startswith("{") and expected.endswith("}"):
                params[expected[1:-1]] = actual
            elif expected != actual:
                return None
        return params

    def _prepare_body(self, route: _Route, json_body: Any) -> Any:
        model = route.request_model
        if model is None or json_body is None:
            return json_body
        try:
            if inspect.isclass(model) and hasattr(model, "model_validate"):
                return model.model_validate(json_body)
            if inspect.isclass(model) and hasattr(model, "parse_obj"):
                return model.parse_obj(json_body)
        except ValidationError as exc:
            raise HTTPException(422, f"Request validation failed: {exc}") from exc
        return json_body

    def _invoke(self, handler: Callable[..., Any], request: Request, params: dict[str, str], body: Any) -> Any:
        signature = inspect.signature(handler)
        arguments: dict[str, Any] = {}
        if "request" in signature.parameters:
            arguments["request"] = request
        if "payload" in signature.parameters:
            arguments["payload"] = body
        elif "body" in signature.parameters:
            arguments["body"] = body
        for key, value in params.items():
            if key in signature.parameters:
                arguments[key] = value
        result = handler(**arguments)
        if inspect.isawaitable(result):
            import asyncio

            return asyncio.run(result)
        return result

    def _to_response(self, result: Any) -> Response:
        if isinstance(result, Response):
            return result
        if isinstance(result, tuple) and len(result) == 2:
            content, status_code = result
            if isinstance(content, str):
                return HTMLResponse(content, status_code=status_code)
            return JSONResponse(content, status_code=status_code)
        if isinstance(result, str):
            return HTMLResponse(result)
        return JSONResponse(result)

    def _cors_headers(self, request_headers: dict[str, str] | None) -> dict[str, str]:
        origin = (request_headers or {}).get("origin") or (request_headers or {}).get("Origin")
        allow_origins: list[str] = []
        allow_methods: list[str] = ["*"]
        allow_headers: list[str] = ["*"]
        allow_credentials = False
        for args, kwargs in self._middleware:
            if args and getattr(args[0], "__name__", "") == "CORSMiddleware":
                allow_origins = list(kwargs.get("allow_origins", []))
                allow_methods = list(kwargs.get("allow_methods", ["*"]))
                allow_headers = list(kwargs.get("allow_headers", ["*"]))
                allow_credentials = bool(kwargs.get("allow_credentials", False))
                break
        if not allow_origins:
            return {}
        if origin and origin not in allow_origins and "*" not in allow_origins:
            return {}
        headers = {
            "Access-Control-Allow-Origin": origin or allow_origins[0],
            "Access-Control-Allow-Methods": ", ".join(allow_methods),
            "Access-Control-Allow-Headers": ", ".join(allow_headers),
        }
        if allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"
        return headers


__all__ = [
    "APIRouter",
    "FastAPI",
    "HTMLResponse",
    "HTTPException",
    "JSONResponse",
    "Request",
    "Response",
]
