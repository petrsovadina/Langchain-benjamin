"""Unit tests for MCP domain entities.

Tests for:
- MCPResponse
- RetryConfig
- MCPHealthStatus
- MCPToolMetadata
"""

from __future__ import annotations

import pytest

# These imports will fail initially (RED phase)
from agent.mcp.domain.entities import MCPResponse, RetryConfig, MCPHealthStatus


class TestMCPResponse:
    """Test MCPResponse value object."""

    def test_successful_response_creation(self):
        """Test creating successful MCPResponse with data."""
        response = MCPResponse(
            success=True,
            data={"drugs": [{"name": "Aspirin", "atc_code": "B01AC06"}]},
            metadata={"latency_ms": 50, "server_url": "http://localhost:3000"}
        )

        assert response.success is True
        assert response.data["drugs"][0]["name"] == "Aspirin"
        assert response.metadata["latency_ms"] == 50
        assert response.error is None

    def test_failed_response_with_error(self):
        """Test creating failed MCPResponse with error message."""
        response = MCPResponse(
            success=False,
            error="Connection timeout",
            metadata={"attempt": 3}
        )

        assert response.success is False
        assert response.error == "Connection timeout"
        assert response.data is None

    def test_failed_response_without_error_raises_valueerror(self):
        """Test that failed response without error raises ValueError."""
        with pytest.raises(ValueError, match="must have error message"):
            MCPResponse(success=False)

    def test_response_immutability(self):
        """Test MCPResponse is frozen (immutable)."""
        response = MCPResponse(success=True, data={})

        with pytest.raises(AttributeError):
            response.success = False  # Should raise FrozenInstanceError

    def test_response_with_empty_metadata(self):
        """Test MCPResponse with default empty metadata."""
        response = MCPResponse(success=True, data={"result": "ok"})

        assert response.metadata == {}
        assert isinstance(response.metadata, dict)

    def test_response_equality(self):
        """Test two MCPResponse instances with same values are equal."""
        response1 = MCPResponse(
            success=True,
            data={"value": 42},
            metadata={"test": True}
        )
        response2 = MCPResponse(
            success=True,
            data={"value": 42},
            metadata={"test": True}
        )

        assert response1 == response2


class TestRetryConfig:
    """Test RetryConfig configuration object."""

    def test_default_retry_config(self):
        """Test RetryConfig with default values."""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 30.0
        assert config.jitter is True
        assert config.exponential_base == 2

    def test_custom_retry_config(self):
        """Test RetryConfig with custom values."""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=60.0,
            jitter=False,
            exponential_base=3
        )

        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 60.0
        assert config.jitter is False
        assert config.exponential_base == 3

    def test_negative_max_retries_raises_valueerror(self):
        """Test that negative max_retries raises ValueError."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            RetryConfig(max_retries=-1)

    def test_zero_base_delay_raises_valueerror(self):
        """Test that base_delay <= 0 raises ValueError."""
        with pytest.raises(ValueError, match="base_delay must be > 0"):
            RetryConfig(base_delay=0.0)

        with pytest.raises(ValueError, match="base_delay must be > 0"):
            RetryConfig(base_delay=-1.0)

    def test_max_delay_less_than_base_delay_raises_valueerror(self):
        """Test that max_delay < base_delay raises ValueError."""
        with pytest.raises(ValueError, match="max_delay must be >= base_delay"):
            RetryConfig(base_delay=10.0, max_delay=5.0)

    def test_retry_config_mutability(self):
        """Test RetryConfig is mutable (not frozen)."""
        config = RetryConfig()

        # Should be able to modify
        config.max_retries = 5
        assert config.max_retries == 5


class TestMCPHealthStatus:
    """Test MCPHealthStatus value object."""

    def test_healthy_status(self):
        """Test healthy MCPHealthStatus."""
        status = MCPHealthStatus(
            status="healthy",
            latency_ms=45,
            tools_count=8
        )

        assert status.status == "healthy"
        assert status.latency_ms == 45
        assert status.tools_count == 8
        assert status.error is None

    def test_unavailable_status(self):
        """Test unavailable MCPHealthStatus with error."""
        status = MCPHealthStatus(
            status="unavailable",
            error="Connection refused"
        )

        assert status.status == "unavailable"
        assert status.error == "Connection refused"
        assert status.latency_ms is None
        assert status.tools_count is None

    def test_timeout_status(self):
        """Test timeout MCPHealthStatus."""
        status = MCPHealthStatus(
            status="timeout",
            error="Health check timeout after 5s"
        )

        assert status.status == "timeout"
        assert status.error == "Health check timeout after 5s"

    def test_unhealthy_status(self):
        """Test unhealthy MCPHealthStatus."""
        status = MCPHealthStatus(
            status="unhealthy",
            latency_ms=5000,
            error="HTTP 503"
        )

        assert status.status == "unhealthy"
        assert status.latency_ms == 5000
        assert status.error == "HTTP 503"

    def test_health_status_immutability(self):
        """Test MCPHealthStatus is frozen (immutable)."""
        status = MCPHealthStatus(status="healthy", latency_ms=50)

        with pytest.raises(AttributeError):
            status.status = "unhealthy"  # Should raise
