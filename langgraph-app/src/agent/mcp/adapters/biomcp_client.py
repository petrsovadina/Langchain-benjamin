"""BioMCP Client adapter - biomedical research database access.

Implements IMCPClient for BioMCP server (Docker-based).

Provides 24 tools, focusing on top 3:
- article_searcher: Search PubMed, bioRxiv, etc.
- get_article_full_text: Get full article text or URL
- search_clinical_trials: Search ClinicalTrials.gov
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import aiohttp
from pydantic import BaseModel, Field, ValidationError

from ..domain.entities import (
    MCPHealthStatus,
    MCPResponse,
    MCPToolMetadata,
    RetryConfig
)
from ..domain.ports import IMCPClient, IRetryStrategy
from ..domain.exceptions import (
    MCPConnectionError,
    MCPTimeoutError,
    MCPValidationError,
    MCPServerError
)

logger = logging.getLogger(__name__)


# Pydantic models for BioMCP responses
class PubMedArticle(BaseModel):
    """Schema for article_searcher response."""
    pmid: str
    title: str
    abstract: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    journal: Optional[str] = None


class ClinicalTrial(BaseModel):
    """Schema for search_clinical_trials response."""
    nct_id: str
    title: str
    status: str
    phase: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)


class BioMCPClient(IMCPClient):
    """Adapter: BioMCP server client.

    Provides access to biomedical research databases (PubMed, Clinical Trials, etc.).

    Attributes:
        base_url: BioMCP server URL (default: http://localhost:8080).
        timeout: Request timeout in seconds (default: 60 - BioMCP can be slow).
        max_results: Default result limit (default: 10).
        retry_strategy: Optional retry implementation.
        default_retry_config: Default RetryConfig with longer delays.

    Example:
        >>> client = BioMCPClient(base_url="http://localhost:8080")
        >>> articles = await client.search_articles("diabetes treatment")
        >>> print(articles[0].title)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout: float = 60.0,
        max_results: int = 10,
        retry_strategy: Optional[IRetryStrategy] = None,
        default_retry_config: Optional[RetryConfig] = None
    ):
        """Initialize BioMCPClient.

        Args:
            base_url: BioMCP server URL.
            timeout: Request timeout in seconds (BioMCP slower than SÚKL).
            max_results: Default maximum results for searches.
            retry_strategy: Optional retry strategy (injected dependency).
            default_retry_config: Default retry configuration.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_results = max_results
        self.retry_strategy = retry_strategy
        self.default_retry_config = default_retry_config or RetryConfig(
            max_retries=3,
            base_delay=2.0  # BioMCP slower, longer delays
        )
        self._session: Optional[aiohttp.ClientSession] = None

        logger.info(f"[BioMCPClient] Initialized with base_url={base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session (lazy initialization).

        Returns:
            Active aiohttp.ClientSession.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            logger.debug("[BioMCPClient] Created new aiohttp session")
        return self._session

    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        retry_config: Optional[RetryConfig] = None
    ) -> MCPResponse:
        """Call BioMCP tool with parameters.

        Args:
            tool_name: Tool identifier (e.g., "article_searcher").
            parameters: Tool parameters.
            retry_config: Override default retry config.

        Returns:
            MCPResponse with success/failure and data.

        Raises:
            MCPConnectionError: Cannot connect to server.
            MCPTimeoutError: Request timeout or rate limiting.
            MCPServerError: Server 5xx error.
        """
        config = retry_config or self.default_retry_config

        async def _execute() -> MCPResponse:
            """Inner function for retry wrapper."""
            session = await self._get_session()
            url = f"{self.base_url}/tools/{tool_name}"

            start_time = datetime.now()

            try:
                logger.debug(
                    f"[BioMCPClient] Calling {tool_name} with {parameters}"
                )

                async with session.post(url, json=parameters) as response:
                    latency_ms = int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    )

                    # Handle server errors (5xx)
                    if response.status >= 500:
                        error_text = await response.text()
                        raise MCPServerError(
                            f"BioMCP server error: {response.status} - {error_text}",
                            status_code=response.status
                        )

                    # Handle rate limiting (429)
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After", "60")
                        raise MCPTimeoutError(
                            f"Rate limited, retry after {retry_after}s",
                            server_url=self.base_url
                        )

                    # Handle client errors (4xx)
                    if response.status >= 400:
                        error_text = await response.text()
                        return MCPResponse(
                            success=False,
                            error=f"HTTP {response.status}: {error_text}",
                            metadata={"latency_ms": latency_ms}
                        )

                    # Success - parse JSON response
                    data = await response.json()

                    return MCPResponse(
                        success=True,
                        data=data,
                        metadata={
                            "latency_ms": latency_ms,
                            "server_url": self.base_url,
                            "tool_name": tool_name
                        }
                    )

            except aiohttp.ClientConnectorError as e:
                raise MCPConnectionError(
                    f"Cannot connect to BioMCP server at {self.base_url}",
                    server_url=self.base_url
                ) from e

            except aiohttp.ServerTimeoutError as e:
                raise MCPTimeoutError(
                    f"BioMCP request timeout after {self.timeout.total}s",
                    server_url=self.base_url
                ) from e

            except ValidationError as e:
                raise MCPValidationError(
                    "Invalid BioMCP response schema",
                    validation_errors=e.errors()
                ) from e

        # Execute with retry if strategy provided
        if self.retry_strategy:
            return await self.retry_strategy.execute_with_retry(_execute, config)
        else:
            return await _execute()

    async def health_check(self, timeout: float = 5.0) -> MCPHealthStatus:
        """Check BioMCP Docker container health.

        Args:
            timeout: Health check timeout in seconds.

        Returns:
            MCPHealthStatus with server state.

        Note:
            Does not raise exceptions - returns status instead.
        """
        try:
            session = await self._get_session()
            start_time = datetime.now()

            async with session.get(
                f"{self.base_url}/health",
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                latency_ms = int(
                    (datetime.now() - start_time).total_seconds() * 1000
                )

                if response.status == 200:
                    data = await response.json()
                    return MCPHealthStatus(
                        status="healthy",
                        latency_ms=latency_ms,
                        tools_count=data.get("tools_count", 24)
                    )
                else:
                    error_text = await response.text()
                    return MCPHealthStatus(
                        status="unhealthy",
                        latency_ms=latency_ms,
                        error=f"HTTP {response.status}: {error_text}"
                    )

        except aiohttp.ClientConnectorError:
            return MCPHealthStatus(
                status="unavailable",
                error="Connection refused"
            )
        except aiohttp.ServerTimeoutError:
            return MCPHealthStatus(
                status="timeout",
                error=f"Health check timeout after {timeout}s"
            )
        except Exception as e:
            return MCPHealthStatus(
                status="unavailable",
                error=f"Unexpected error: {str(e)}"
            )

    async def list_tools(self) -> List[MCPToolMetadata]:
        """List available BioMCP tools.

        Returns:
            List of BioMCP tool metadata (24 total, showing top 3).

        Note:
            Currently returns hardcoded list. Future: query /tools endpoint.
        """
        return [
            MCPToolMetadata(
                name="article_searcher",
                description="Search PubMed, bioRxiv, and other databases",
                parameters={"query": "string", "max_results": "int"},
                returns={"articles": "list[PubMedArticle]"}
            ),
            MCPToolMetadata(
                name="get_article_full_text",
                description="Get full article text or open access URL",
                parameters={"pmid": "string"},
                returns={"full_text": "string", "url": "string"}
            ),
            MCPToolMetadata(
                name="search_clinical_trials",
                description="Search ClinicalTrials.gov database",
                parameters={"query": "string"},
                returns={"trials": "list[ClinicalTrial]"}
            ),
            # ... 21 more tools not shown for brevity
        ]

    async def close(self) -> None:
        """Close aiohttp session gracefully."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("[BioMCPClient] Session closed")

    # High-level helper methods (typed convenience API)

    async def search_articles(
        self,
        query: str,
        max_results: Optional[int] = None
    ) -> List[PubMedArticle]:
        """Search PubMed articles (typed helper).

        Args:
            query: Search query (e.g., "diabetes treatment").
            max_results: Limit results (default: self.max_results).

        Returns:
            List of PubMed articles with abstracts.

        Raises:
            MCPConnectionError, MCPTimeoutError: Connection issues.
            MCPValidationError: Invalid response.
        """
        response = await self.call_tool(
            "article_searcher",
            {
                "query": query,
                "max_results": max_results or self.max_results
            }
        )

        if not response.success:
            raise MCPValidationError(f"Article search failed: {response.error}")

        # Validate with Pydantic
        try:
            return [
                PubMedArticle(**article)
                for article in response.data.get("articles", [])
            ]
        except ValidationError as e:
            raise MCPValidationError(
                "Invalid article search response",
                validation_errors=e.errors()
            ) from e

    async def get_full_text(self, pmid: str) -> Optional[str]:
        """Get article full text or URL.

        Args:
            pmid: PubMed ID.

        Returns:
            Full text string or open access URL, None if not available.

        Note:
            Does not raise on failure - returns None instead.
        """
        response = await self.call_tool("get_article_full_text", {"pmid": pmid})

        if not response.success:
            return None

        # Return full_text if available, otherwise URL
        return response.data.get("full_text") or response.data.get("url")

    async def search_trials(self, query: str) -> List[ClinicalTrial]:
        """Search clinical trials.

        Args:
            query: Search query (e.g., "cancer immunotherapy").

        Returns:
            List of clinical trials from ClinicalTrials.gov.

        Raises:
            MCPConnectionError, MCPTimeoutError: Connection issues.
            MCPValidationError: Invalid response.
        """
        response = await self.call_tool("search_clinical_trials", {"query": query})

        if not response.success:
            raise MCPValidationError(f"Trial search failed: {response.error}")

        # Validate with Pydantic
        try:
            return [
                ClinicalTrial(**trial)
                for trial in response.data.get("trials", [])
            ]
        except ValidationError as e:
            raise MCPValidationError(
                "Invalid trial search response",
                validation_errors=e.errors()
            ) from e
