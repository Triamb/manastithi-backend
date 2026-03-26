"""
Simple in-memory rate limiter for Manastithi API.
No external dependencies needed (Redis not required for small scale).
"""

import time
from collections import defaultdict
from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self):
        # {key: [(timestamp, ...)] }
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old(self, key: str, window_seconds: int):
        cutoff = time.time() - window_seconds
        self._requests[key] = [
            t for t in self._requests[key] if t > cutoff
        ]

    def check(self, key: str, max_requests: int, window_seconds: int):
        """Check if request is allowed. Raises 429 if rate limited."""
        self._clean_old(key, window_seconds)

        if len(self._requests[key]) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )

        self._requests[key].append(time.time())


# Singleton
rate_limiter = RateLimiter()


def rate_limit_by_ip(
    max_requests: int = 30,
    window_seconds: int = 60,
):
    """FastAPI dependency for rate limiting by IP address."""
    async def _check(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"ip:{client_ip}:{request.url.path}"
        rate_limiter.check(key, max_requests, window_seconds)
    return _check


# Pre-configured rate limits for different endpoint types
chat_rate_limit = rate_limit_by_ip(max_requests=15, window_seconds=60)
email_rate_limit = rate_limit_by_ip(max_requests=5, window_seconds=60)
calendar_rate_limit = rate_limit_by_ip(max_requests=10, window_seconds=60)
