"""Minimal CORS middleware configuration shim."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CORSMiddleware:
    allow_origins: list[str] = field(default_factory=list)
    allow_methods: list[str] = field(default_factory=lambda: ["*"])
    allow_headers: list[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = False
