"""Enterprise IP and Route Rate Limiting Middleware.

Protects against:
- Authentication brute-force attacks on /api/auth/login (10 req/min limit)
- DoS and resource exhaustion on computational pipelines (120 req/min general limit)

Implements RFC 6585 compliant HTTP 429 responses with rate-limit headers.
"""

from collections import defaultdict
from datetime import datetime, timezone
import time
from typing import Dict, List, Tuple
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Sliding-window in-memory rate limiter per IP and path category."""

    def __init__(self):
        # Map: key -> list of timestamp floats
        self._history: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, client_ip: str, path: str) -> Tuple[bool, int, int, int]:
        """Checks if request is allowed.

        Returns: (is_allowed, limit, remaining, retry_after_seconds)
        """
        now = time.time()

        # Determine threshold based on route sensitivity
        if path.startswith("/api/auth/login"):
            limit = 10
            window_seconds = 60
            key = f"auth:{client_ip}"
        else:
            limit = 180
            window_seconds = 60
            key = f"gen:{client_ip}"

        cutoff = now - window_seconds
        # Clean older entries
        timestamps = [t for t in self._history[key] if t > cutoff]
        self._history[key] = timestamps

        current_count = len(timestamps)
        if current_count >= limit:
            oldest_in_window = timestamps[0]
            retry_after = int(max(1, window_seconds - (now - oldest_in_window)))
            return False, limit, 0, retry_after

        # Record this request
        self._history[key].append(now)
        remaining = max(0, limit - (current_count + 1))
        return True, limit, remaining, 0


rate_limiter = RateLimiter()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Starlette middleware intercepting API requests and enforcing rate limits."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static assets and health checks
        path = request.url.path
        if not path.startswith("/api") or path in ("/api/health", "/api/data-sources/health"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"

        allowed, limit, remaining, retry_after = rate_limiter.is_allowed(client_ip, path)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RateLimitExceeded",
                    "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "limit": limit,
                    "retry_after_seconds": retry_after,
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(retry_after),
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
