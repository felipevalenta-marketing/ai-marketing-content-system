"""In-memory security rate limiter."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from threading import RLock
from time import time
from typing import Any

from .security_config import SecurityConfig


@dataclass
class RateLimitRule:
    limit: int
    window_seconds: int = 3600


class RateLimiter:
    def __init__(self) -> None:
        self._lock = RLock()
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def _rule_for_role(self, role: str, config: SecurityConfig | None = None) -> RateLimitRule:
        cfg = config or SecurityConfig()
        normalized = str(role or "anonymous").strip().lower()
        if normalized == "admin":
            return RateLimitRule(limit=cfg.admin_rate_limit_per_hour)
        if normalized in {"authenticated", "user", "manager", "editor", "viewer"}:
            return RateLimitRule(limit=cfg.authenticated_rate_limit_per_hour)
        return RateLimitRule(limit=cfg.anonymous_rate_limit_per_hour)

    def allow_request(self, identity: str, role: str = "anonymous", *, config: SecurityConfig | None = None) -> dict[str, Any]:
        rule = self._rule_for_role(role, config=config)
        if (config or SecurityConfig()).enable_rate_limit_test_mode:
            return {
                "allowed": True,
                "limit": rule.limit,
                "remaining": rule.limit,
                "window_seconds": rule.window_seconds,
                "identity": identity,
                "role": role,
            }
        key = f"{str(identity or 'anonymous').strip().lower()}|{str(role or 'anonymous').strip().lower()}"
        now = time()
        with self._lock:
            bucket = self._requests.setdefault(key, deque())
            while bucket and now - bucket[0] > rule.window_seconds:
                bucket.popleft()
            allowed = len(bucket) < rule.limit
            if allowed:
                bucket.append(now)
        return {
            "allowed": allowed,
            "limit": rule.limit,
            "remaining": max(0, rule.limit - len(bucket)),
            "window_seconds": rule.window_seconds,
            "identity": identity,
            "role": role,
        }

    def reset(self) -> None:
        with self._lock:
            self._requests.clear()


_RATE_LIMITER = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    return _RATE_LIMITER
