"""
Application middleware:
  - Request logging (method, path, user, status, duration)
  - AI rate limiting (20 requests/hour per user; Redis or in-memory)
  - Global error handling wired in main.py via exception_handler
"""
import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_token

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("finlit")

# ── AI rate limit ──────────────────────────────────────────────────────────────
AI_RATE_LIMIT = 20      # max AI calls per window per user
AI_RATE_WINDOW = 3600   # 1 hour

# In-memory fallback when Redis is unavailable: user_id -> [call_timestamp, ...]
_rate_store: dict[str, list[float]] = defaultdict(list)


async def check_ai_rate_limit(user_id: str) -> bool:
    """Return True if the call is allowed; False if the hourly limit is exceeded."""
    from app.core.cache import get_redis

    redis = get_redis()
    key = f"ai_rate:{user_id}"

    if redis:
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, AI_RATE_WINDOW)
            return int(count) <= AI_RATE_LIMIT
        except Exception:
            pass

    # In-memory sliding-window fallback
    now = time.time()
    cutoff = now - AI_RATE_WINDOW
    calls = [t for t in _rate_store[user_id] if t > cutoff]
    if len(calls) >= AI_RATE_LIMIT:
        _rate_store[user_id] = calls
        return False
    calls.append(now)
    _rate_store[user_id] = calls
    return True


# ── Logging middleware ─────────────────────────────────────────────────────────
def _jwt_user_id(request: Request) -> str:
    """Extract user id from Bearer token for logging only. Never raises."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        payload = decode_token(auth[7:])
        if payload:
            return payload.get("sub", "anon")[:8]
    return "anon"


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.monotonic()
        user_id = _jwt_user_id(request)
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "UNHANDLED %s %s [user:%s] — %s",
                request.method, request.url.path, user_id, exc,
                exc_info=True,
            )
            return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})

        duration_ms = (time.monotonic() - start) * 1000
        level = logging.WARNING if response.status_code >= 400 else logging.INFO
        logger.log(
            level,
            "%s %s [user:%s] → %d (%.0fms)",
            request.method,
            request.url.path,
            user_id,
            response.status_code,
            duration_ms,
        )
        return response
