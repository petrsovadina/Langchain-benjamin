"""MCP domain ports - abstract interfaces for MCP operations.

Ports define contracts (interfaces) that adapters must implement.
This follows Hexagonal Architecture pattern - domain is independent
of external implementations.

Ports:
- IMCPClient: Abstract MCP client interface
- IRetryStrategy: Abstract retry behavior interface
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .entities import MCPHealthStatus, MCPResponse, MCPToolMetadata, RetryConfig


class IMCPClient(ABC):
    """Port: Abstract MCP client interface.

    Defines contract for all MCP server interactions.
    Implementations: SUKLMCPClient, BioMCPClient.

    This interface allows:
    - Swapping MCP implementations (localhost ↔ production)
    - Mocking for tests without real servers
    - Polymorphic usage in LangGraph nodes

    Example:
        >>> class MySUKLClient(IMCPClient):
        ...     async def call_tool(self, tool_name, parameters, retry_config=None):
        ...         # Implementation
        ...         pass
    """

    @abstractmethod
    async def call_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        retry_config: RetryConfig | None = None,
    ) -> MCPResponse:
        """Call MCP tool with parameters.

        Args:
            tool_name: MCP tool identifier (e.g., "search_drugs").
            parameters: Tool-specific parameters.
            retry_config: Override default retry config.

        Returns:
            MCPResponse with success/failure and data.

        Raises:
            MCPConnectionError: Cannot connect to server.
            MCPTimeoutError: Request exceeded timeout.
            MCPValidationError: Invalid parameters or response.
        """
        pass

    @abstractmethod
    async def health_check(self, timeout: float = 5.0) -> MCPHealthStatus:
        """Check MCP server health.

        Args:
            timeout: Maximum wait time in seconds (default: 5.0).

        Returns:
            MCPHealthStatus with server state.

        Note:
            Should not raise exceptions - return status="unavailable" instead.
        """
        pass

    @abstractmethod
    async def list_tools(self) -> List[MCPToolMetadata]:
        """Discover available MCP tools.

        Returns:
            List of tool metadata for documentation/debugging.

        Note:
            May return empty list if server doesn't support tool discovery.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close client connections gracefully.

        Should cleanup:
        - HTTP sessions (aiohttp)
        - Connection pools
        - Any background tasks
        """
        pass


class IRetryStrategy(ABC):
    """Port: Abstract retry strategy interface.

    Defines contract for retry behavior with backoff.
    Implementation: TenacityRetryStrategy.

    Allows swapping retry implementations:
    - Exponential backoff
    - Linear backoff
    - No retry (for testing)

    Example:
        >>> class MyRetryStrategy(IRetryStrategy):
        ...     async def execute_with_retry(self, operation, config):
        ...         # Implementation with tenacity
        ...         pass
    """

    @abstractmethod
    async def execute_with_retry(
        self,
        operation: Any,  # Async callable
        config: RetryConfig,
    ) -> Any:
        """Execute async operation with retry logic.

        Args:
            operation: Async function/coroutine to retry.
            config: Retry configuration (max_retries, delays, etc.).

        Returns:
            Operation result if successful.

        Raises:
            Original exception after max retries exhausted.

        Note:
            Should only retry transient errors:
            - MCPConnectionError (network issues)
            - MCPTimeoutError (including rate limiting)
            - MCPServerError (5xx errors)

            Should NOT retry:
            - MCPValidationError (client-side error)
            - 4xx errors (except 429)
        """
        pass
