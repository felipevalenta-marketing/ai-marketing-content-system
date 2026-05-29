"""Authentication contracts."""

from __future__ import annotations

from typing import Any


AUTH_RESULT_CONTRACT: dict[str, Any] = {
    "success": False,
    "user": {},
    "token": "",
    "warnings": [],
    "errors": [],
}

JWT_PAYLOAD_CONTRACT: dict[str, Any] = {
    "sub": "",
    "email": "",
    "exp": "",
}
