"""Tests for Redis cache layer (US8).

Verifies:
- Cache miss returns None
- Cache hit returns data
- Redis unavailable graceful degradation
- Full SHA-256 cache key generation (post-T018)
- Invalidation uses scan_iter instead of keys
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from redis.exceptions import RedisError

from api.cache import (
    generate_cache_key,
    get_cached_response,
    invalidate_cache,
    set_cached_response,
)


class TestGenerateCacheKey:
    """Test cache key generation."""

    def test_full_sha256_hash(self):
        """Cache key must contain full 64-char SHA-256 hash (not truncated)."""
        key = generate_cache_key("test query", "quick")
        # Format: "consult:{64-char-hash}:quick"
        parts = key.split(":")
        assert parts[0] == "consult"
        assert len(parts[1]) == 64  # Full SHA-256 hex digest
        assert parts[2] == "quick"

    def test_different_queries_different_keys(self):
        """Different queries must produce different cache keys."""
        key1 = generate_cache_key("metformin", "quick")
        key2 = generate_cache_key("ibuprofen", "quick")
        assert key1 != key2

    def test_different_modes_different_keys(self):
        """Same query with different modes must produce different keys."""
        key1 = generate_cache_key("test", "quick")
        key2 = generate_cache_key("test", "deep")
        assert key1 != key2


class TestGetCachedResponse:
    """Test cache retrieval."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        client = AsyncMock()
        return client

    async def test_cache_miss_returns_none(self, mock_redis):
        """Cache miss must return None."""
        mock_redis.get.return_value = None
        with patch("api.cache.get_redis_client", return_value=mock_redis):
            result = await get_cached_response("unknown query", "quick")
        assert result is None

    async def test_cache_hit_returns_data(self, mock_redis):
        """Cache hit must return parsed JSON data."""
        cached = {"answer": "Metformin je...", "retrieved_docs": []}
        mock_redis.get.return_value = json.dumps(cached)
        with patch("api.cache.get_redis_client", return_value=mock_redis):
            result = await get_cached_response("test", "quick")
        assert result == cached

    async def test_redis_unavailable_returns_none(self):
        """When Redis is unavailable, must return None (graceful degradation)."""
        with patch("api.cache.get_redis_client", return_value=None):
            result = await get_cached_response("test", "quick")
        assert result is None

    async def test_redis_error_returns_none(self, mock_redis):
        """When Redis raises an error, must return None."""
        mock_redis.get.side_effect = RedisError("Connection lost")
        with patch("api.cache.get_redis_client", return_value=mock_redis):
            result = await get_cached_response("test", "quick")
        assert result is None


class TestSetCachedResponse:
    """Test cache storage."""

    async def test_set_calls_setex(self):
        """set_cached_response must call Redis setex with TTL."""
        mock_redis = AsyncMock()
        data = {"answer": "test"}
        with patch("api.cache.get_redis_client", return_value=mock_redis):
            await set_cached_response("query", "quick", data, ttl=3600)
        mock_redis.setex.assert_called_once()

    async def test_set_redis_unavailable_no_error(self):
        """When Redis is unavailable, set must silently skip."""
        with patch("api.cache.get_redis_client", return_value=None):
            await set_cached_response("query", "quick", {"answer": "test"})


class TestInvalidateCache:
    """Test cache invalidation."""

    async def test_invalidate_uses_scan_iter(self):
        """Invalidation must use scan_iter instead of keys command."""
        mock_redis = AsyncMock()

        async def mock_scan_iter(**kwargs):
            yield "consult:abc:quick"
            yield "consult:def:deep"

        mock_redis.scan_iter = mock_scan_iter
        mock_redis.delete = AsyncMock(return_value=1)

        with patch("api.cache.get_redis_client", return_value=mock_redis):
            deleted = await invalidate_cache("consult:*")

        assert deleted == 2
        assert mock_redis.delete.call_count == 2

    async def test_invalidate_redis_unavailable_returns_zero(self):
        """When Redis is unavailable, invalidation must return 0."""
        with patch("api.cache.get_redis_client", return_value=None):
            result = await invalidate_cache()
        assert result == 0
