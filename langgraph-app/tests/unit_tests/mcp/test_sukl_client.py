"""Unit tests for SUKLMCPClient adapter.

Tests use aioresponses to mock HTTP calls without real SÚKL-mcp server.
"""

from __future__ import annotations

import pytest
from aioresponses import aioresponses
import aiohttp

from agent.mcp.adapters.sukl_client import SUKLMCPClient
from agent.mcp.domain.entities import RetryConfig
from agent.mcp.domain.exceptions import (
    MCPConnectionError,
    MCPTimeoutError,
    MCPServerError,
    MCPValidationError
)


class TestSUKLMCPClientInitialization:
    """Test SUKLMCPClient initialization and configuration."""

    def test_init_with_default_parameters(self):
        """Test SUKLMCPClient creation with defaults."""
        client = SUKLMCPClient()

        assert client.base_url == "http://localhost:3000"
        assert client.timeout.total == 30.0
        assert client.default_retry_config.max_retries == 3

    def test_init_with_custom_base_url(self):
        """Test SUKLMCPClient with custom base_url."""
        client = SUKLMCPClient(base_url="http://custom-sukl:4000")

        assert client.base_url == "http://custom-sukl:4000"

    def test_init_with_custom_timeout(self):
        """Test SUKLMCPClient with custom timeout."""
        client = SUKLMCPClient(timeout=60.0)

        assert client.timeout.total == 60.0

    def test_init_with_custom_retry_config(self):
        """Test SUKLMCPClient with custom RetryConfig."""
        config = RetryConfig(max_retries=5, base_delay=2.0)
        client = SUKLMCPClient(default_retry_config=config)

        assert client.default_retry_config.max_retries == 5
        assert client.default_retry_config.base_delay == 2.0

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        client = SUKLMCPClient(base_url="http://localhost:3000/")

        assert client.base_url == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_lazy_session_initialization(self):
        """Test that aiohttp session is created lazily."""
        client = SUKLMCPClient()

        # Session should be None initially
        assert client._session is None

        # Getting session should create it
        session = await client._get_session()
        assert session is not None
        assert isinstance(session, aiohttp.ClientSession)

        await client.close()

    @pytest.mark.asyncio
    async def test_session_reuse(self):
        """Test that same session is reused."""
        client = SUKLMCPClient()

        session1 = await client._get_session()
        session2 = await client._get_session()

        assert session1 is session2

        await client.close()


class TestSUKLMCPClientCallTool:
    """Test SUKLMCPClient.call_tool method."""

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call returns MCPResponse."""
        with aioresponses() as m:
            m.post(
                "http://localhost:3000/tools/search_drugs",
                payload={
                    "drugs": [
                        {
                            "name": "Aspirin",
                            "atc_code": "B01AC06",
                            "registration_number": "12345"
                        }
                    ]
                },
                status=200
            )

            client = SUKLMCPClient()
            response = await client.call_tool(
                "search_drugs",
                {"query": "aspirin"}
            )

            assert response.success is True
            assert response.data["drugs"][0]["name"] == "Aspirin"
            assert response.error is None
            assert "latency_ms" in response.metadata

            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_connection_error(self):
        """Test connection error raises MCPConnectionError."""
        with aioresponses() as m:
            m.post(
                "http://localhost:3000/tools/test_tool",
                exception=aiohttp.ClientConnectorError(
                    connection_key=None,
                    os_error=OSError("Connection refused")
                )
            )

            client = SUKLMCPClient()

            with pytest.raises(MCPConnectionError, match="Cannot connect"):
                await client.call_tool("test_tool", {})

            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_timeout_error(self):
        """Test timeout raises MCPTimeoutError."""
        with aioresponses() as m:
            m.post(
                "http://localhost:3000/tools/test_tool",
                exception=aiohttp.ServerTimeoutError()
            )

            client = SUKLMCPClient()

            with pytest.raises(MCPTimeoutError, match="timeout"):
                await client.call_tool("test_tool", {})

            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_server_error_500(self):
        """Test 500 server error raises MCPServerError."""
        with aioresponses() as m:
            m.post(
                "http://localhost:3000/tools/test_tool",
                status=500,
                body="Internal Server Error"
            )

            client = SUKLMCPClient()

            with pytest.raises(MCPServerError) as exc_info:
                await client.call_tool("test_tool", {})

            assert exc_info.value.status_code == 500

            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_rate_limiting_429(self):
        """Test 429 rate limiting raises MCPTimeoutError."""
        with aioresponses() as m:
            m.post(
                "http://localhost:3000/tools/test_tool",
                status=429,
                headers={"Retry-After": "60"}
            )

            client = SUKLMCPClient()

            with pytest.raises(MCPTimeoutError, match="Rate limited"):
                await client.call_tool("test_tool", {})

            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_client_error_400(self):
        """Test 400 client error returns failed MCPResponse."""
        with aioresponses() as m:
            m.post(
                "http://localhost:3000/tools/test_tool",
                status=400,
                body="Bad Request: Invalid parameters"
            )

            client = SUKLMCPClient()
            response = await client.call_tool("test_tool", {})

            assert response.success is False
            assert "400" in response.error
            assert response.data is None

            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_includes_metadata(self):
        """Test response includes timing metadata."""
        with aioresponses() as m:
            m.post(
                "http://localhost:3000/tools/test_tool",
                payload={"result": "ok"},
                status=200
            )

            client = SUKLMCPClient()
            response = await client.call_tool("test_tool", {})

            assert "latency_ms" in response.metadata
            assert "server_url" in response.metadata
            assert response.metadata["server_url"] == "http://localhost:3000"
            assert "tool_name" in response.metadata

            await client.close()


class TestSUKLMCPClientHealthCheck:
    """Test SUKLMCPClient.health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check returns healthy status."""
        with aioresponses() as m:
            m.get(
                "http://localhost:3000/health",
                payload={"status": "ok", "tools_count": 8},
                status=200
            )

            client = SUKLMCPClient()
            status = await client.health_check()

            assert status.status == "healthy"
            assert status.latency_ms is not None
            assert status.latency_ms < 1000
            assert status.tools_count == 8
            assert status.error is None

            await client.close()

    @pytest.mark.asyncio
    async def test_health_check_unavailable(self):
        """Test health check handles connection refused."""
        with aioresponses() as m:
            m.get(
                "http://localhost:3000/health",
                exception=aiohttp.ClientConnectorError(
                    connection_key=None,
                    os_error=OSError("Connection refused")
                )
            )

            client = SUKLMCPClient()
            status = await client.health_check()

            assert status.status == "unavailable"
            assert status.error == "Connection refused"
            assert status.latency_ms is None

            await client.close()

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check handles timeout."""
        with aioresponses() as m:
            m.get(
                "http://localhost:3000/health",
                exception=aiohttp.ServerTimeoutError()
            )

            client = SUKLMCPClient()
            status = await client.health_check(timeout=3.0)

            assert status.status == "timeout"
            assert "timeout" in status.error.lower()

            await client.close()

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_status(self):
        """Test health check handles non-200 status."""
        with aioresponses() as m:
            m.get(
                "http://localhost:3000/health",
                status=503,
                body="Service Unavailable"
            )

            client = SUKLMCPClient()
            status = await client.health_check()

            assert status.status == "unhealthy"
            assert "503" in status.error

            await client.close()


class TestSUKLMCPClientClose:
    """Test SUKLMCPClient.close method."""

    @pytest.mark.asyncio
    async def test_close_without_session(self):
        """Test close when session was never created."""
        client = SUKLMCPClient()
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_with_active_session(self):
        """Test close properly closes aiohttp session."""
        client = SUKLMCPClient()
        session = await client._get_session()

        assert not session.closed

        await client.close()

        assert session.closed
