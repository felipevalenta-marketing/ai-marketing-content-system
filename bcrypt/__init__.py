"""Local bcrypt-compatible shim used for offline verification.

This module provides the tiny subset of the ``bcrypt`` API used by the
project. It uses PBKDF2-HMAC-SHA256 under the hood so the interface stays
available even when the native bcrypt wheel is not installed in the sandbox.
"""

from __future__ import annotations

from base64 import urlsafe_b64encode, urlsafe_b64decode
import hashlib
import hmac
import os
from typing import Any

DEFAULT_ROUNDS = 12
SALT_SIZE = 16


def gensalt(rounds: int = DEFAULT_ROUNDS) -> bytes:
    rounds = max(4, min(31, int(rounds or DEFAULT_ROUNDS)))
    salt = os.urandom(SALT_SIZE)
    return f"$pbkdf2-sha256${rounds}${urlsafe_b64encode(salt).decode('ascii')}".encode("utf-8")


def hashpw(password: bytes | str, salt: bytes | str) -> bytes:
    password_bytes = _to_bytes(password)
    salt_text = _to_text(salt)
    parts = salt_text.split("$")
    if len(parts) < 4:
        raise ValueError("Invalid salt format.")
    rounds = int(parts[2] or DEFAULT_ROUNDS)
    raw_salt = urlsafe_b64decode(parts[3].encode("ascii"))
    digest = hashlib.pbkdf2_hmac("sha256", password_bytes, raw_salt, rounds * 10000)
    encoded = urlsafe_b64encode(digest).decode("ascii")
    return f"$pbkdf2-sha256${rounds}${parts[3]}${encoded}".encode("utf-8")


def checkpw(password: bytes | str, hashed_password: bytes | str) -> bool:
    hashed_text = _to_text(hashed_password)
    parts = hashed_text.split("$")
    if len(parts) < 5:
        return False
    candidate = hashpw(password, "$".join(parts[:4]).encode("utf-8"))
    return hmac.compare_digest(_to_text(candidate), hashed_text)


def _to_bytes(value: bytes | str) -> bytes:
    return value if isinstance(value, bytes) else str(value).encode("utf-8")


def _to_text(value: bytes | str) -> str:
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)
