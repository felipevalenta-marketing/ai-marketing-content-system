"""JWT helper functions using HMAC-SHA256."""

from __future__ import annotations

from base64 import urlsafe_b64encode, urlsafe_b64decode
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest, new as hmac_new
import json
import os
from typing import Any


def _secret(secret: str | None = None) -> str:
    value = str(secret or os.getenv("JWT_SECRET_KEY", "")).strip()
    return value


def create_access_token(payload: dict[str, Any], expires_in_hours: int = 24, secret: str | None = None) -> str:
    signing_secret = _secret(secret)
    if not signing_secret:
        return ""
    header = {"alg": "HS256", "typ": "JWT"}
    now = datetime.now(timezone.utc)
    body = dict(payload or {})
    hours = int(expires_in_hours or 24)
    body.setdefault("exp", int((now + timedelta(hours=hours)).timestamp()))
    encoded_header = _encode_json(header)
    encoded_payload = _encode_json(body)
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = _sign(signing_input, signing_secret)
    return f"{encoded_header}.{encoded_payload}.{signature}"


def verify_access_token(token: str, secret: str | None = None) -> dict[str, Any]:
    payload = decode_access_token(token, secret=secret)
    if not payload:
        return {"valid": False, "payload": {}, "errors": ["Invalid token."], "warnings": []}
    exp = payload.get("exp")
    if isinstance(exp, str) and exp.isdigit():
        exp = int(exp)
    if isinstance(exp, (int, float)) and int(exp) < int(datetime.now(timezone.utc).timestamp()):
        return {"valid": False, "payload": payload, "errors": ["Token expired."], "warnings": []}
    return {"valid": True, "payload": payload, "errors": [], "warnings": []}


def decode_access_token(token: str, secret: str | None = None) -> dict[str, Any]:
    signing_secret = _secret(secret)
    if not signing_secret or not token:
        return {}
    try:
        header_text, payload_text, signature = str(token).split(".", 2)
        signing_input = f"{header_text}.{payload_text}".encode("utf-8")
        if not compare_digest(signature, _sign(signing_input, signing_secret)):
            return {}
        payload = _decode_json(payload_text)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _encode_json(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _decode_json(value: str) -> Any:
    raw = value.encode("ascii")
    padding = b"=" * (-len(raw) % 4)
    decoded = urlsafe_b64decode(raw + padding)
    return json.loads(decoded.decode("utf-8"))


def _sign(signing_input: bytes, secret: str) -> str:
    digest = hmac_new(secret.encode("utf-8"), signing_input, sha256).digest()
    return urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
