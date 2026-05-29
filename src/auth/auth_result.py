"""Structured auth results."""

from __future__ import annotations

from typing import Any


def build_success_result(*, user: dict[str, Any] | None = None, access_token: str = "", token_type: str = "bearer", warnings: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": True,
        "user": user or {},
        "access_token": access_token,
        "token_type": token_type,
        "warnings": list(warnings or []),
        "errors": [],
        "metadata": dict(metadata or {}),
    }


def build_failure_result(message: str, *, user: dict[str, Any] | None = None, access_token: str = "", token_type: str = "bearer", warnings: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "success": False,
        "user": user or {},
        "access_token": access_token,
        "token_type": token_type,
        "warnings": list(warnings or []),
        "errors": [message],
        "metadata": dict(metadata or {}),
    }
