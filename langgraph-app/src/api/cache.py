"""Redis caching layer for frequent queries.

Features:
    - TTL-based expiration (1 hour default)
    - LRU eviction policy
    - Cache key hashing (query → hash)
    - Cache hit/miss metrics
    - Graceful degradation (cache unavailable → bypass)
"""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis
from redis.asyncio import Redis
from redis.exceptions import RedisError

from api.config import settings

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Redis | None = None


async def get_redis_client() -> Redis | None:
    """Get or create Redis client.

    Returns:
        Redis client or None if unavailable (graceful degradation).
    """
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=50,
            )
            # Test connection
            await _redis_client.ping()
            logger.info("✅ Redis cache connected")
        except RedisError as e:
            logger.warning(f"⚠️  Redis cache unavailable: {e}")
            _redis_client = None

    return _redis_client


def generate_cache_key(query: str, mode: str) -> str:
    """Generate cache key from query and mode.

    Uses SHA256 hash to ensure consistent key length.

    Args:
        query: User query text.
        mode: Execution mode (quick/deep).

    Returns:
        Cache key (e.g., "consult:abc123def456:quick").
    """
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
    return f"consult:{query_hash}:{mode}"


async def get_cached_response(query: str, mode: str) -> dict[str, Any] | None:
    """Get cached response for query.

    Args:
        query: User query text.
        mode: Execution mode.

    Returns:
        Cached response dict or None if cache miss.
    """
    client = await get_redis_client()
    if client is None:
        return None  # Cache unavailable

    try:
        cache_key = generate_cache_key(query, mode)
        cached_data = await client.get(cache_key)

        if cached_data:
            logger.info(f"✅ Cache HIT: {cache_key}")
            return json.loads(cached_data)
        else:
            logger.debug(f"❌ Cache MISS: {cache_key}")
            return None
    except RedisError as e:
        logger.warning(f"Redis get error: {e}")
        return None  # Graceful degradation


async def set_cached_response(
    query: str,
    mode: str,
    response: dict[str, Any],
    ttl: int = settings.cache_ttl,
) -> None:
    """Cache response for query.

    Args:
        query: User query text.
        mode: Execution mode.
        response: Response dict to cache.
        ttl: Time-to-live in seconds (default 1 hour).
    """
    client = await get_redis_client()
    if client is None:
        return  # Cache unavailable

    try:
        cache_key = generate_cache_key(query, mode)
        await client.setex(
            cache_key,
            ttl,
            json.dumps(response, ensure_ascii=False),
        )
        logger.info(f"💾 Cached response: {cache_key} (TTL: {ttl}s)")
    except RedisError as e:
        logger.warning(f"Redis set error: {e}")


async def invalidate_cache(pattern: str = "consult:*") -> int:
    """Invalidate cache entries matching pattern.

    Args:
        pattern: Redis key pattern (default: all consult queries).

    Returns:
        Number of keys deleted.
    """
    client = await get_redis_client()
    if client is None:
        return 0

    try:
        keys = await client.keys(pattern)
        if keys:
            deleted = await client.delete(*keys)
            logger.info(f"🗑️  Invalidated {deleted} cache entries")
            return deleted
        return 0
    except RedisError as e:
        logger.warning(f"Redis invalidate error: {e}")
        return 0
