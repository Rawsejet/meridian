"""Redis connection and session management."""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.core.config import Settings, get_settings

_pool = None


def get_pool(settings: Settings | None = None) -> ConnectionPool:
    """Get Redis connection pool."""
    global _pool
    if _pool is None:
        _settings = settings or get_settings()
        _pool = ConnectionPool.from_url(
            _settings.redis_url,
            decode_responses=False,
            max_connections=20,
        )
    return _pool


@asynccontextmanager
async def get_redis(
    settings: Settings | None = None,
) -> AsyncGenerator[redis.Redis, None]:
    """Get Redis connection (context manager)."""
    pool = get_pool(settings)
    client = redis.Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.close()


async def get_redis_value(key: str) -> bytes | None:
    """Get a value from Redis."""
    async with get_redis() as r:
        return await r.get(key)


async def set_redis_value(
    key: str, value: bytes, expire: int | None = None
) -> bool:
    """Set a value in Redis with optional expiration."""
    async with get_redis() as r:
        if expire:
            return await r.set(key, value, ex=expire)
        return await r.set(key, value)


async def delete_redis_value(key: str) -> int:
    """Delete a key from Redis. Returns number of keys deleted."""
    async with get_redis() as r:
        return await r.delete(key)


async def clear_all_keys(pattern: str = "*") -> int:
    """Delete all keys matching pattern. Use with caution!"""
    async with get_redis() as r:
        keys = await r.keys(pattern)
        if keys:
            return await r.delete(*keys)
        return 0