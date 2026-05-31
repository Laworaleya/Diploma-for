import json
from typing import Optional
import redis.asyncio as aioredis
from app.config import settings

_redis: aioredis.Redis = None

DEFAULT_TTL = 3600  # 1 hour


async def connect_cache():
    """Initialize Redis connection on app startup."""
    global _redis
    
    if not settings.REDIS_URI:
        print("ℹ️ Redis URI is empty. Caching disabled.")
        _redis = None
        return

    try:
        _redis = aioredis.from_url(
            settings.REDIS_URI,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=5,
        )
        await _redis.ping()
        print("✅ Redis connected")
    except Exception:
        print("ℹ️ Redis недоступен, кэш отключён")
        _redis = None


async def close_cache():
    """Close Redis connection on app shutdown."""
    global _redis
    if _redis:
        await _redis.close()
        print("🔌 Redis connection closed")


def get_redis() -> Optional[aioredis.Redis]:
    """Get Redis instance (may be None if unavailable)."""
    return _redis


async def get_cached(key: str) -> Optional[dict]:
    """Get cached value by key. Returns None if not found or Redis unavailable."""
    if not _redis:
        return None
    try:
        data = await _redis.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


async def set_cached(key: str, value: dict, ttl: int = DEFAULT_TTL):
    """Set cached value with TTL. Silently fails if Redis unavailable."""
    if not _redis:
        return
    try:
        await _redis.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        pass


async def invalidate(pattern: str):
    """Delete cached keys matching pattern."""
    if not _redis:
        return
    try:
        keys = []
        async for key in _redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await _redis.delete(*keys)
    except Exception:
        pass
