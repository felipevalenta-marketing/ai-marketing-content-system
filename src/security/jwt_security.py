"""JWT hardening helpers."""

from __future__ import annotations

from base64 import urlsafe_b64decode
from datetime import datetime, timezone
from typing import Any
import json
import os
import re

from src.auth.jwt_manager import verify_access_token
from src.reports.markdown_utils import safe_text


def _decode_segment(segment: str) -> dict[str, Any]:
    raw = segment.encode("ascii")
    padding = b"=" * (-len(raw) % 4)
    decoded = urlsafe_b64decode(raw + padding)
    payload = json.loads(decoded.decode("utf-8"))
    return payload if isinstance(payload, dict) else {}


def validate_jwt_security(token: str, secret: str | None = None, *, issuer: str | None = None, algorithms: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    normalized_token = safe_text(token, limit=8192).strip()
    signing_secret = str(secret or os.getenv("JWT_SECRET_KEY", "")).strip()
    allowed_algorithms = [str(item).strip().upper() for item in (algorithms or ["HS256"]) if str(item).strip()]
    if len(signing_secret) < 16:
        errors.append("JWT secret is too short.")
    if not normalized_token or normalized_token.count(".") != 2:
        errors.append("Malformed JWT.")
        return {"valid": False, "warnings": warnings, "errors": errors, "payload": {}, "header": {}}
    try:
        header_segment, payload_segment, _signature = normalized_token.split(".", 2)
        header = _decode_segment(header_segment)
    except Exception:
        errors.append("Malformed JWT.")
        return {"valid": False, "warnings": warnings, "errors": errors, "payload": {}, "header": {}}
    algorithm = str(header.get("alg", "")).upper()
    if algorithm not in allowed_algorithms:
        errors.append("Unsupported JWT algorithm.")
    verification = verify_access_token(normalized_token, secret=signing_secret)
    payload = dict(verification.get("payload", {}) or {})
    if issuer:
        token_issuer = str(payload.get("iss", "")).strip()
        if token_issuer and token_issuer != issuer:
            errors.append("Invalid JWT issuer.")
    exp = payload.get("exp")
    if isinstance(exp, str) and exp.isdigit():
        exp = int(exp)
    if isinstance(exp, (int, float)) and int(exp) < int(datetime.now(timezone.utc).timestamp()):
        errors.append("Token expired.")
    if not verification.get("valid"):
        errors.extend([message for message in verification.get("errors", []) if message not in errors])
    return {"valid": not errors, "warnings": warnings, "errors": errors, "payload": payload, "header": header, "algorithm": algorithm}


def build_jwt_security_summary(token: str, secret: str | None = None, *, issuer: str | None = None) -> dict[str, Any]:
    result = validate_jwt_security(token, secret=secret, issuer=issuer)
    return {
        "valid": bool(result.get("valid")),
        "algorithm": result.get("algorithm", ""),
        "warnings": list(result.get("warnings", [])),
        "errors": list(result.get("errors", [])),
        "payload": result.get("payload", {}),
    }

