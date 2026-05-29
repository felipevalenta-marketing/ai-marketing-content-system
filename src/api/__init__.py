"""REST API package for the AI Marketing Content System."""

from __future__ import annotations

from typing import Any

__all__ = ["app", "create_app"]


def create_app(*args: Any, **kwargs: Any) -> Any:
    """Import the API app factory lazily to avoid package import cycles."""

    from src.api.main import create_app as api_create_app

    return api_create_app(*args, **kwargs)


def __getattr__(name: str) -> Any:
    if name == "app":
        from src.api.main import app as api_app

        return api_app
    if name == "create_app":
        return create_app
    raise AttributeError(name)
