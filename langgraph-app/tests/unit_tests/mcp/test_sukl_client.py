"""Unit tests for SUKLMCPClient adapter (JSON-RPC protocol).

Tests use aioresponses to mock HTTP calls without real SÚKL-mcp server.
Updated 2026-02-09: Rewrote for JSON-RPC protocol.
"""

from __future__ import annotations

import aiohttp
import pytest
from aioresponses import aioresponses

from agent.mcp.adapters.sukl_client import SUKLMCPClient
from agent.mcp.domain.entities import RetryConfig
from agent.mcp.domain.exceptions import (
    MCPConnectionError,
    MCPServerError,
    MCPTimeoutError,
)

BASE_URL = "https://sukl-mcp-ts.vercel.app/mcp"


class TestSUKLMCPClientInitialization:
    """Test SUKLMCPClient initialization and configuration."""

    def test_init_with_default_parameters(self):
        """Test SUKLMCPClient creation with defaults."""
        client = SUKLMCPClient(base_url=BASE_URL)
        assert client.base_url == BASE_URL
        assert client.timeout.total == 30.0
        assert client.default_retry_config.max_retries == 3

    def test_init_with_custom_base_url(self):
        client = SUKLMCPClient(base_url="http://custom-sukl:4000")
        assert client.base_url == "http://custom-sukl:4000"

    def test_init_with_custom_timeout(self):
        client = SUKLMCPClient(base_url=BASE_URL, timeout=60.0)
        assert client.timeout.total == 60.0

    def test_init_with_custom_retry_config(self):
        config = RetryConfig(max_retries=5, base_delay=2.0)
        client = SUKLMCPClient(base_url=BASE_URL, default_retry_config=config)
        assert client.default_retry_config.max_retries == 5
        assert client.default_retry_config.base_delay == 2.0

    def test_base_url_trailing_slash_removed(self):
        client = SUKLMCPClient(base_url="http://localhost:3000/")
        assert client.base_url == "http://localhost:3000"

    @pytest.mark.asyncio
    async def test_lazy_session_initialization(self):
        client = SUKLMCPClient(base_url=BASE_URL)
        assert client._session is None
        session = await client._get_session()
        assert session is not None
        assert isinstance(session, aiohttp.ClientSession)
        await client.close()

    @pytest.mark.asyncio
    async def test_session_reuse(self):
        client = SUKLMCPClient(base_url=BASE_URL)
        session1 = await client._get_session()
        session2 = await client._get_session()
        assert session1 is session2
        await client.close()


class TestSUKLMCPClientCallTool:
    """Test SUKLMCPClient.call_tool with JSON-RPC protocol."""

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful JSON-RPC tool call."""
        with aioresponses() as m:
            m.post(
                BASE_URL,
                payload={
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": 'Found 1 medicine:\n\n1. Aspirin (12345) - acetylsalicylic acid',
                            }
                        ]
                    },
                    "id": 1,
                },
                status=200,
            )

            client = SUKLMCPClient(base_url=BASE_URL)
            response = await client.call_tool("search_drugs", {"query": "aspirin"})

            assert response.success is True
            assert "drugs" in response.data
            assert response.error is None
            assert "latency_ms" in response.metadata
            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_connection_error(self):
        """Test connection error raises MCPConnectionError."""
        with aioresponses() as m:
            m.post(
                BASE_URL,
                exception=aiohttp.ClientConnectorError(
                    connection_key=None, os_error=OSError("Connection refused")
                ),
            )

            client = SUKLMCPClient(base_url=BASE_URL)
            with pytest.raises(MCPConnectionError, match="Cannot connect"):
                await client.call_tool("search_drugs", {"query": "test"})
            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_timeout_error(self):
        """Test timeout raises MCPTimeoutError."""
        with aioresponses() as m:
            m.post(BASE_URL, exception=aiohttp.ServerTimeoutError())

            client = SUKLMCPClient(base_url=BASE_URL)
            with pytest.raises(MCPTimeoutError, match="timeout"):
                await client.call_tool("search_drugs", {"query": "test"})
            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_server_error_500(self):
        """Test 500 raises MCPServerError."""
        with aioresponses() as m:
            m.post(BASE_URL, status=500, body="Internal Server Error")

            client = SUKLMCPClient(base_url=BASE_URL)
            with pytest.raises(MCPServerError, match="SÚKL server error"):
                await client.call_tool("search_drugs", {"query": "test"})
            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_rate_limiting_429(self):
        """Test 429 raises MCPTimeoutError."""
        with aioresponses() as m:
            m.post(BASE_URL, status=429, headers={"Retry-After": "30"})

            client = SUKLMCPClient(base_url=BASE_URL)
            with pytest.raises(MCPTimeoutError, match="Rate limited"):
                await client.call_tool("search_drugs", {"query": "test"})
            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_client_error_400(self):
        """Test 400 returns failed MCPResponse (no exception)."""
        with aioresponses() as m:
            m.post(BASE_URL, status=400, body="Bad Request")

            client = SUKLMCPClient(base_url=BASE_URL)
            response = await client.call_tool("search_drugs", {"query": "test"})

            assert response.success is False
            assert "400" in response.error
            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_includes_metadata(self):
        """Test that successful calls include metadata."""
        with aioresponses() as m:
            m.post(
                BASE_URL,
                payload={
                    "jsonrpc": "2.0",
                    "result": {"content": [{"type": "text", "text": "No results"}]},
                    "id": 1,
                },
                status=200,
            )

            client = SUKLMCPClient(base_url=BASE_URL)
            response = await client.call_tool("search_drugs", {"query": "xyz"})

            assert "latency_ms" in response.metadata
            assert response.metadata["server_url"] == BASE_URL
            assert response.metadata["tool_name"] == "search-medicine"
            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_jsonrpc_error(self):
        """Test JSON-RPC error response returns failed MCPResponse."""
        with aioresponses() as m:
            m.post(
                BASE_URL,
                payload={
                    "jsonrpc": "2.0",
                    "error": {"code": -32602, "message": "Invalid params"},
                    "id": 1,
                },
                status=200,
            )

            client = SUKLMCPClient(base_url=BASE_URL)
            response = await client.call_tool("search_drugs", {"query": "test"})

            assert response.success is False
            assert "Invalid params" in response.error
            await client.close()

    @pytest.mark.asyncio
    async def test_tool_name_mapping(self):
        """Test internal tool names are mapped to MCP server names."""
        client = SUKLMCPClient(base_url=BASE_URL)
        mcp_tool, _ = client._map_tool_and_params("search_drugs", {"query": "test"})
        assert mcp_tool == "search-medicine"

        mcp_tool, _ = client._map_tool_and_params("get_drug_details", {"registration_number": "123"})
        assert mcp_tool == "get-medicine-details"

        mcp_tool, _ = client._map_tool_and_params("get_pricing_info", {"registration_number": "123"})
        assert mcp_tool == "get-reimbursement"
        await client.close()


class TestSUKLMCPClientHealthCheck:
    """Test SUKLMCPClient.health_check via JSON-RPC tools/list."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        with aioresponses() as m:
            m.post(
                BASE_URL,
                payload={
                    "jsonrpc": "2.0",
                    "result": {"tools": [{"name": "search-medicine"}, {"name": "get-medicine-details"}]},
                    "id": 1,
                },
                status=200,
            )

            client = SUKLMCPClient(base_url=BASE_URL)
            status = await client.health_check()

            assert status.status == "healthy"
            assert status.tools_count == 2
            assert status.latency_ms >= 0
            await client.close()

    @pytest.mark.asyncio
    async def test_health_check_unavailable(self):
        with aioresponses() as m:
            m.post(
                BASE_URL,
                exception=aiohttp.ClientConnectorError(
                    connection_key=None, os_error=OSError("Connection refused")
                ),
            )

            client = SUKLMCPClient(base_url=BASE_URL)
            status = await client.health_check()

            assert status.status == "unavailable"
            assert "Connection refused" in status.error
            await client.close()

    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        with aioresponses() as m:
            m.post(BASE_URL, exception=aiohttp.ServerTimeoutError())

            client = SUKLMCPClient(base_url=BASE_URL)
            status = await client.health_check()

            assert status.status == "timeout"
            await client.close()

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_status(self):
        with aioresponses() as m:
            m.post(BASE_URL, status=503, body="Service Unavailable")

            client = SUKLMCPClient(base_url=BASE_URL)
            status = await client.health_check()

            assert status.status == "unhealthy"
            assert "503" in status.error
            await client.close()


class TestSUKLMCPClientListTools:
    """Test SUKLMCPClient.list_tools."""

    @pytest.mark.asyncio
    async def test_list_tools_from_server(self):
        with aioresponses() as m:
            m.post(
                BASE_URL,
                payload={
                    "jsonrpc": "2.0",
                    "result": {
                        "tools": [
                            {"name": "search-medicine", "description": "Search drugs", "inputSchema": {"properties": {"query": {"type": "string"}}}},
                        ]
                    },
                    "id": 1,
                },
                status=200,
            )

            client = SUKLMCPClient(base_url=BASE_URL)
            tools = await client.list_tools()

            assert len(tools) == 1
            assert tools[0].name == "search-medicine"
            await client.close()

    @pytest.mark.asyncio
    async def test_list_tools_fallback(self):
        """Test fallback to hardcoded list when server fails."""
        with aioresponses() as m:
            m.post(BASE_URL, exception=aiohttp.ServerTimeoutError())

            client = SUKLMCPClient(base_url=BASE_URL)
            tools = await client.list_tools()

            assert len(tools) == 8  # Hardcoded fallback
            tool_names = [t.name for t in tools]
            assert "search-medicine" in tool_names
            await client.close()
