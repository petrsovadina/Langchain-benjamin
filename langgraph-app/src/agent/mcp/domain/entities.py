"""MCP domain entities - framework-independent business models.

This module contains pure Python dataclasses representing MCP domain concepts.
No external dependencies (aiohttp, pydantic, etc.) - only standard library.

Entities:
- MCPResponse: Standardized response from MCP operations
- MCPHealthStatus: Health check result
- RetryConfig: Configuration for exponential backoff retry
- MCPToolMetadata: Metadata about available MCP tools
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal


@dataclass(frozen=True)
class MCPResponse:
    """Standardized response from any MCP tool.

    Immutable value object representing MCP operation result.
    Used by all MCP clients (SÚKL, BioMCP) for consistent error handling.

    Attributes:
        success: Whether operation succeeded.
        data: Response payload (typed by caller).
        error: Error message if failed.
        metadata: Timing, server info, debug data.

    Raises:
        ValueError: If success=False but no error message provided.

    Example:
        >>> response = MCPResponse(
        ...     success=True,
        ...     data={"drugs": [{"name": "Aspirin"}]},
        ...     metadata={"latency_ms": 50}
        ... )
        >>> response.success
        True
    """

    success: bool
    data: Any = None
    error: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate business invariants.

        Ensures failed responses have error messages.
        """
        if not self.success and not self.error:
            raise ValueError("Failed MCPResponse must have error message")


@dataclass(frozen=True)
class MCPHealthStatus:
    """Health check result from MCP server.

    Value object for monitoring and diagnostics.
    Returned by IMCPClient.health_check() method.

    Attributes:
        status: Server health state.
        latency_ms: Response time in milliseconds.
        tools_count: Number of available tools.
        error: Error message if unhealthy.

    Example:
        >>> status = MCPHealthStatus(
        ...     status="healthy",
        ...     latency_ms=45,
        ...     tools_count=8
        ... )
        >>> status.status
        'healthy'
    """

    status: Literal["healthy", "unhealthy", "unavailable", "timeout"]
    latency_ms: int | None = None
    tools_count: int | None = None
    error: str | None = None


@dataclass
class RetryConfig:
    """Configuration for exponential backoff retry strategy.

    Mutable configuration object (not frozen - allows runtime tweaking).
    Used by TenacityRetryStrategy to control retry behavior.

    Attributes:
        max_retries: Maximum retry attempts (default: 3).
        base_delay: Initial delay in seconds (default: 1.0).
        max_delay: Maximum delay cap in seconds (default: 30.0).
        jitter: Add randomness to prevent thundering herd (default: True).
        exponential_base: Multiplier for exponential backoff (default: 2).

    Raises:
        ValueError: If configuration violates constraints.

    Example:
        >>> config = RetryConfig(max_retries=5, base_delay=2.0)
        >>> config.max_retries
        5
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: bool = True
    exponential_base: int = 2

    def __post_init__(self) -> None:
        """Validate configuration constraints."""
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.base_delay <= 0:
            raise ValueError("base_delay must be > 0")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")


@dataclass(frozen=True)
class MCPToolMetadata:
    """Metadata about available MCP tool.

    Used for tool discovery and documentation.
    Returned by IMCPClient.list_tools() method.

    Attributes:
        name: Tool identifier (e.g., "search_drugs").
        description: Human-readable description.
        parameters: Expected parameter schema.
        returns: Return value schema.

    Example:
        >>> metadata = MCPToolMetadata(
        ...     name="search_drugs",
        ...     description="Search drugs by name or keyword",
        ...     parameters={"query": "string"},
        ...     returns={"drugs": "list[DrugSearchResult]"}
        ... )
        >>> metadata.name
        'search_drugs'
    """

    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    returns: Dict[str, Any] = field(default_factory=dict)
