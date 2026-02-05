"""SÚKL MCP Client adapter - Czech pharmaceutical database access.

Implements IMCPClient for SÚKL-mcp server (https://github.com/petrsovadina/SUKL-mcp).

Provides 8 tools:
- search_drugs: Search drugs by name
- get_drug_details: Get detailed drug information
- search_by_atc: Search by ATC code
- get_interactions: Get drug interactions
- search_side_effects: Search side effects
- get_pricing_info: Get pricing information
- search_by_ingredient: Search by active ingredient
- validate_prescription: Validate prescription
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, cast

import aiohttp
from pydantic import BaseModel, ValidationError

from ..domain.entities import MCPHealthStatus, MCPResponse, MCPToolMetadata, RetryConfig
from ..domain.exceptions import (
    MCPConnectionError,
    MCPServerError,
    MCPTimeoutError,
    MCPValidationError,
)
from ..domain.ports import IMCPClient, IRetryStrategy

logger = logging.getLogger(__name__)


# Pydantic models for SÚKL responses
class DrugSearchResult(BaseModel):
    """Schema for search_drugs response."""

    name: str
    atc_code: str
    registration_number: str
    manufacturer: str | None = None


class SUKLMCPClient(IMCPClient):
    """Adapter: SÚKL-mcp server client.

    Provides access to Czech pharmaceutical database with 68,000+ drugs.

    Attributes:
        base_url: SÚKL-mcp server URL (default: http://localhost:3000).
        timeout: Request timeout in seconds (default: 30).
        retry_strategy: Optional retry implementation.
        default_retry_config: Default RetryConfig for all calls.

    Example:
        >>> client = SUKLMCPClient(base_url="http://localhost:3000")
        >>> response = await client.call_tool(
        ...     "search_drugs",
        ...     {"query": "aspirin"}
        ... )
        >>> print(response.data)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        timeout: float = 30.0,
        retry_strategy: IRetryStrategy | None = None,
        default_retry_config: RetryConfig | None = None,
    ):
        """Initialize SUKLMCPClient.

        Args:
            base_url: SÚKL-mcp server URL.
            timeout: Request timeout in seconds.
            retry_strategy: Optional retry strategy (injected dependency).
            default_retry_config: Default retry configuration.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retry_strategy = retry_strategy
        self.default_retry_config = default_retry_config or RetryConfig()
        self._session: aiohttp.ClientSession | None = None

        logger.info(f"[SUKLMCPClient] Initialized with base_url={base_url}")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session (lazy initialization).

        Returns:
            Active aiohttp.ClientSession.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            logger.debug("[SUKLMCPClient] Created new aiohttp session")
        return self._session

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        retry_config: RetryConfig | None = None,
    ) -> MCPResponse:
        """Call SÚKL MCP tool with parameters.

        Args:
            tool_name: Tool identifier (e.g., "search_drugs").
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
                logger.debug(f"[SUKLMCPClient] Calling {tool_name} with {parameters}")

                async with session.post(url, json=parameters) as response:
                    latency_ms = int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    )

                    # Handle server errors (5xx)
                    if response.status >= 500:
                        error_text = await response.text()
                        raise MCPServerError(
                            f"SÚKL server error: {response.status} - {error_text}",
                            status_code=response.status,
                        )

                    # Handle rate limiting (429)
                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After", "60")
                        raise MCPTimeoutError(
                            f"Rate limited, retry after {retry_after}s",
                            server_url=self.base_url,
                        )

                    # Handle client errors (4xx)
                    if response.status >= 400:
                        error_text = await response.text()
                        return MCPResponse(
                            success=False,
                            error=f"HTTP {response.status}: {error_text}",
                            metadata={"latency_ms": latency_ms},
                        )

                    # Success - parse JSON response
                    data = await response.json()

                    return MCPResponse(
                        success=True,
                        data=data,
                        metadata={
                            "latency_ms": latency_ms,
                            "server_url": self.base_url,
                            "tool_name": tool_name,
                        },
                    )

            except aiohttp.ClientConnectorError as e:
                raise MCPConnectionError(
                    f"Cannot connect to SÚKL server at {self.base_url}",
                    server_url=self.base_url,
                ) from e

            except aiohttp.ServerTimeoutError as e:
                raise MCPTimeoutError(
                    f"SÚKL request timeout after {self.timeout.total}s",
                    server_url=self.base_url,
                ) from e

            except ValidationError as e:
                raise MCPValidationError(
                    "Invalid SÚKL response schema", validation_errors=e.errors()
                ) from e

        # Execute with retry if strategy provided
        if self.retry_strategy:
            result = await self.retry_strategy.execute_with_retry(_execute, config)
            return cast(MCPResponse, result)
        else:
            return await _execute()

    async def health_check(self, timeout: float = 5.0) -> MCPHealthStatus:
        """Check SÚKL server health.

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
                f"{self.base_url}/health", timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                if response.status == 200:
                    data = await response.json()
                    return MCPHealthStatus(
                        status="healthy",
                        latency_ms=latency_ms,
                        tools_count=data.get("tools_count", 8),
                    )
                else:
                    error_text = await response.text()
                    return MCPHealthStatus(
                        status="unhealthy",
                        latency_ms=latency_ms,
                        error=f"HTTP {response.status}: {error_text}",
                    )

        except aiohttp.ClientConnectorError:
            return MCPHealthStatus(status="unavailable", error="Connection refused")
        except aiohttp.ServerTimeoutError:
            return MCPHealthStatus(
                status="timeout", error=f"Health check timeout after {timeout}s"
            )
        except Exception as e:
            return MCPHealthStatus(
                status="unavailable", error=f"Unexpected error: {str(e)}"
            )

    async def list_tools(self) -> list[MCPToolMetadata]:
        """List available SÚKL MCP tools.

        Returns:
            List of 8 SÚKL tool metadata.

        Note:
            Currently returns hardcoded list. Future: query /tools endpoint.
        """
        return [
            MCPToolMetadata(
                name="search_drugs",
                description="Search drugs by name or keyword",
                parameters={"query": "string"},
                returns={"drugs": "list[DrugSearchResult]"},
            ),
            MCPToolMetadata(
                name="get_drug_details",
                description="Get detailed drug information",
                parameters={"registration_number": "string"},
                returns={"drug": "DrugDetails"},
            ),
            MCPToolMetadata(
                name="search_by_atc",
                description="Search drugs by ATC code",
                parameters={"atc_code": "string"},
                returns={"drugs": "list[DrugSearchResult]"},
            ),
            MCPToolMetadata(
                name="get_interactions",
                description="Get drug interactions",
                parameters={"drug_id": "string"},
                returns={"interactions": "list[Interaction]"},
            ),
            MCPToolMetadata(
                name="search_side_effects",
                description="Search drug side effects",
                parameters={"drug_id": "string"},
                returns={"side_effects": "list[SideEffect]"},
            ),
            MCPToolMetadata(
                name="get_pricing_info",
                description="Get drug pricing information",
                parameters={"registration_number": "string"},
                returns={"pricing": "PricingInfo"},
            ),
            MCPToolMetadata(
                name="search_by_ingredient",
                description="Search drugs by active ingredient",
                parameters={"ingredient": "string"},
                returns={"drugs": "list[DrugSearchResult]"},
            ),
            MCPToolMetadata(
                name="validate_prescription",
                description="Validate prescription data",
                parameters={"prescription": "dict"},
                returns={"valid": "bool", "errors": "list[str]"},
            ),
        ]

    async def close(self) -> None:
        """Close aiohttp session gracefully."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("[SUKLMCPClient] Session closed")

    # High-level helper methods (typed convenience API)

    async def search_drugs(self, query: str) -> list[DrugSearchResult]:
        """Search drugs by name (typed helper).

        Args:
            query: Drug name or keyword.

        Returns:
            List of matching drugs.

        Raises:
            MCPConnectionError, MCPTimeoutError: Connection issues.
            MCPValidationError: Invalid response.
        """
        response = await self.call_tool("search_drugs", {"query": query})

        if not response.success:
            raise MCPValidationError(f"Drug search failed: {response.error}")

        # Validate with Pydantic
        try:
            return [DrugSearchResult(**drug) for drug in response.data.get("drugs", [])]
        except ValidationError as e:
            raise MCPValidationError(
                "Invalid drug search response", validation_errors=e.errors()
            ) from e
