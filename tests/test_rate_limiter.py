from __future__ import annotations

from src.security.rate_limiter import RateLimiter


def test_rate_limiter_blocks_after_limit(monkeypatch) -> None:
    monkeypatch.setenv("ANONYMOUS_RATE_LIMIT_PER_HOUR", "1")
    limiter = RateLimiter()
    first = limiter.allow_request("anon")
    second = limiter.allow_request("anon")
    assert first["allowed"] is True
    assert second["allowed"] is False


def test_rate_limiter_test_mode_bypasses_limits(monkeypatch) -> None:
    monkeypatch.setenv("ENABLE_RATE_LIMIT_TEST_MODE", "true")
    limiter = RateLimiter()
    first = limiter.allow_request("anon")
    second = limiter.allow_request("anon")
    assert first["allowed"] is True
    assert second["allowed"] is True
