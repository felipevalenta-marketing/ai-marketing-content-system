from __future__ import annotations

from src.security.security_headers import build_security_headers


def test_security_headers_include_core_protections() -> None:
    headers = build_security_headers(production=False)
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "Content-Security-Policy" in headers
    assert "Strict-Transport-Security" not in headers


def test_security_headers_include_hsts_in_production() -> None:
    headers = build_security_headers(production=True)
    assert headers["Strict-Transport-Security"].startswith("max-age=31536000")

