"""Command-line interface package for the AI Marketing Content System."""

from __future__ import annotations

from typing import Any

__all__ = ["main"]


def main(*args: Any, **kwargs: Any) -> Any:
    """Import the CLI entrypoint lazily to avoid package import cycles."""

    from src.cli.cli_app import main as cli_main

    return cli_main(*args, **kwargs)
