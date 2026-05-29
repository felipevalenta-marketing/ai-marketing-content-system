"""API error helpers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class ApiError(HTTPException):
    """Readable API error wrapper."""


def raise_bad_request(message: str, *, status_code: int = 400) -> None:
    raise ApiError(status_code=status_code, detail=message)


def error_response_message(message: Any) -> str:
    return str(message or "Request failed.")
