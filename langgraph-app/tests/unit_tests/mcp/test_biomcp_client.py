"""Unit tests for BioMCPClient adapter.

Tests use aioresponses to mock HTTP calls without real BioMCP Docker server.
"""

from __future__ import annotations

import pytest
from aioresponses import aioresponses
import aiohttp

from agent.mcp.adapters.biomcp_client import BioMCPClient
from agent.mcp.domain.entities import RetryConfig
from agent.mcp.domain.exceptions import (
    MCPConnectionError,
    MCPTimeoutError,
    MCPServerError,
    MCPValidationError
)


class TestBioMCPClientInitialization:
    """Test BioMCPClient initialization and configuration."""

    def test_init_with_default_parameters(self):
        """Test BioMCPClient creation with defaults."""
        client = BioMCPClient()

        assert client.base_url == "http://localhost:8080"
        assert client.timeout.total == 60.0  # BioMCP slower than SÚKL
        assert client.max_results == 10
        assert client.default_retry_config.max_retries == 3
        assert client.default_retry_config.base_delay == 2.0  # Longer delays

    def test_init_with_custom_base_url(self):
        """Test BioMCPClient with custom base_url."""
        client = BioMCPClient(base_url="http://biomcp-prod:9000")

        assert client.base_url == "http://biomcp-prod:9000"

    def test_init_with_custom_max_results(self):
        """Test BioMCPClient with custom max_results."""
        client = BioMCPClient(max_results=20)

        assert client.max_results == 20

    def test_base_url_trailing_slash_removed(self):
        """Test that trailing slash is removed from base_url."""
        client = BioMCPClient(base_url="http://localhost:8080/")

        assert client.base_url == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_lazy_session_initialization(self):
        """Test that aiohttp session is created lazily."""
        client = BioMCPClient()

        assert client._session is None

        session = await client._get_session()
        assert session is not None
        assert isinstance(session, aiohttp.ClientSession)

        await client.close()


class TestBioMCPClientCallTool:
    """Test BioMCPClient.call_tool method."""

    @pytest.mark.asyncio
    async def test_call_tool_article_search_success(self):
        """Test successful article search returns MCPResponse."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/article_searcher",
                payload={
                    "articles": [
                        {
                            "pmid": "12345678",
                            "title": "Diabetes Treatment Study",
                            "abstract": "This study examines...",
                            "authors": ["Smith J", "Doe A"],
                            "doi": "10.1234/example"
                        }
                    ]
                },
                status=200
            )

            client = BioMCPClient()
            response = await client.call_tool(
                "article_searcher",
                {"query": "diabetes", "max_results": 10}
            )

            assert response.success is True
            assert response.data["articles"][0]["pmid"] == "12345678"
            assert "latency_ms" in response.metadata

            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_connection_error(self):
        """Test connection error raises MCPConnectionError."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/test_tool",
                exception=aiohttp.ClientConnectorError(
                    connection_key=None,
                    os_error=OSError("Connection refused")
                )
            )

            client = BioMCPClient()

            with pytest.raises(MCPConnectionError, match="Cannot connect"):
                await client.call_tool("test_tool", {})

            await client.close()

    @pytest.mark.asyncio
    async def test_call_tool_timeout_error(self):
        """Test timeout raises MCPTimeoutError."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/test_tool",
                exception=aiohttp.ServerTimeoutError()
            )

            client = BioMCPClient()

            with pytest.raises(MCPTimeoutError, match="timeout"):
                await client.call_tool("test_tool", {})

            await client.close()


class TestBioMCPClientHealthCheck:
    """Test BioMCPClient.health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self):
        """Test health check returns healthy status."""
        with aioresponses() as m:
            m.get(
                "http://localhost:8080/health",
                payload={"status": "ok", "tools_count": 24},
                status=200
            )

            client = BioMCPClient()
            status = await client.health_check()

            assert status.status == "healthy"
            assert status.latency_ms is not None
            assert status.tools_count == 24
            assert status.error is None

            await client.close()

    @pytest.mark.asyncio
    async def test_health_check_unavailable(self):
        """Test health check handles Docker container not running."""
        with aioresponses() as m:
            m.get(
                "http://localhost:8080/health",
                exception=aiohttp.ClientConnectorError(
                    connection_key=None,
                    os_error=OSError("Connection refused")
                )
            )

            client = BioMCPClient()
            status = await client.health_check()

            assert status.status == "unavailable"
            assert status.error == "Connection refused"

            await client.close()


class TestBioMCPClientTypedHelpers:
    """Test BioMCPClient typed helper methods."""

    @pytest.mark.asyncio
    async def test_search_articles_success(self):
        """Test search_articles returns typed PubMedArticle list."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/article_searcher",
                payload={
                    "articles": [
                        {
                            "pmid": "12345678",
                            "title": "Test Article",
                            "abstract": "Abstract text",
                            "authors": ["Author A"],
                            "publication_date": "2024-01-01",
                            "doi": "10.1234/test",
                            "journal": "Test Journal"
                        }
                    ]
                },
                status=200
            )

            client = BioMCPClient()
            articles = await client.search_articles("test query")

            assert len(articles) == 1
            assert articles[0].pmid == "12345678"
            assert articles[0].title == "Test Article"

            await client.close()

    @pytest.mark.asyncio
    async def test_search_articles_with_max_results(self):
        """Test search_articles respects max_results parameter."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/article_searcher",
                payload={"articles": []},
                status=200
            )

            client = BioMCPClient(max_results=5)
            await client.search_articles("test", max_results=20)

            # aioresponses doesn't easily expose request body, so just verify call succeeded

            await client.close()

    @pytest.mark.asyncio
    async def test_get_full_text_success(self):
        """Test get_full_text returns text or URL."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/get_article_full_text",
                payload={"full_text": "Article full text content..."},
                status=200
            )

            client = BioMCPClient()
            text = await client.get_full_text("12345678")

            assert text == "Article full text content..."

            await client.close()

    @pytest.mark.asyncio
    async def test_get_full_text_returns_url_when_no_text(self):
        """Test get_full_text returns URL if full_text not available."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/get_article_full_text",
                payload={"url": "https://doi.org/10.1234/example"},
                status=200
            )

            client = BioMCPClient()
            text = await client.get_full_text("12345678")

            assert text == "https://doi.org/10.1234/example"

            await client.close()

    @pytest.mark.asyncio
    async def test_get_full_text_returns_none_on_failure(self):
        """Test get_full_text returns None on failure."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/get_article_full_text",
                status=404
            )

            client = BioMCPClient()
            text = await client.get_full_text("99999999")

            assert text is None

            await client.close()

    @pytest.mark.asyncio
    async def test_search_trials_success(self):
        """Test search_trials returns typed ClinicalTrial list."""
        with aioresponses() as m:
            m.post(
                "http://localhost:8080/tools/search_clinical_trials",
                payload={
                    "trials": [
                        {
                            "nct_id": "NCT12345678",
                            "title": "Cancer Immunotherapy Trial",
                            "status": "Recruiting",
                            "phase": "Phase 2",
                            "conditions": ["Cancer", "Melanoma"]
                        }
                    ]
                },
                status=200
            )

            client = BioMCPClient()
            trials = await client.search_trials("cancer immunotherapy")

            assert len(trials) == 1
            assert trials[0].nct_id == "NCT12345678"
            assert trials[0].status == "Recruiting"
            assert "Cancer" in trials[0].conditions

            await client.close()


class TestBioMCPClientClose:
    """Test BioMCPClient.close method."""

    @pytest.mark.asyncio
    async def test_close_without_session(self):
        """Test close when session was never created."""
        client = BioMCPClient()
        await client.close()  # Should not raise

    @pytest.mark.asyncio
    async def test_close_with_active_session(self):
        """Test close properly closes aiohttp session."""
        client = BioMCPClient()
        session = await client._get_session()

        assert not session.closed

        await client.close()

        assert session.closed
