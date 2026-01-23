"""MCP configuration from environment variables.

Provides MCPConfig dataclass for loading MCP infrastructure settings
from .env file with sensible defaults.

Following Constitution:
- Principle II (Type Safety): Fully typed dataclass
- Principle V (Modular): Configuration separated from implementation

Usage:
    from agent.mcp.config import MCPConfig

    config = MCPConfig.from_env()
    sukl_client = SUKLMCPClient(
        base_url=config.sukl_url,
        timeout=config.sukl_timeout,
        default_retry_config=config.to_retry_config()
    )
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .domain.entities import RetryConfig


@dataclass(frozen=True)
class MCPConfig:
    """MCP infrastructure configuration.

    Immutable configuration object loaded from environment variables.
    All values have sensible defaults for local development.

    Attributes:
        sukl_url: SÚKL-mcp server URL.
        sukl_timeout: SÚKL request timeout in seconds.
        biomcp_url: BioMCP server URL.
        biomcp_timeout: BioMCP request timeout in seconds.
        biomcp_max_results: Default max results for BioMCP searches.
        max_retries: Maximum retry attempts for transient errors.
        retry_base_delay: Initial retry delay in seconds.
        retry_max_delay: Maximum retry delay cap in seconds.
        retry_jitter: Whether to add randomness to retry delays.

    Example:
        >>> config = MCPConfig.from_env()
        >>> print(config.sukl_url)
        'http://localhost:3000'
    """

    # SÚKL MCP server
    sukl_url: str
    sukl_timeout: float

    # BioMCP server
    biomcp_url: str
    biomcp_timeout: float
    biomcp_max_results: int

    # Retry configuration
    max_retries: int
    retry_base_delay: float
    retry_max_delay: float
    retry_jitter: bool

    @classmethod
    def from_env(cls) -> MCPConfig:
        """Load configuration from environment variables.

        Reads MCP-related environment variables with fallback to defaults.
        Boolean values accept 'true'/'false' (case-insensitive).

        Returns:
            MCPConfig with values from environment or defaults.

        Example:
            >>> import os
            >>> os.environ['SUKL_MCP_URL'] = 'http://prod:3000'
            >>> config = MCPConfig.from_env()
            >>> config.sukl_url
            'http://prod:3000'
        """
        return cls(
            # SÚKL configuration
            sukl_url=os.getenv("SUKL_MCP_URL", "http://localhost:3000"),
            sukl_timeout=float(os.getenv("SUKL_MCP_TIMEOUT", "30.0")),
            # BioMCP configuration
            biomcp_url=os.getenv("BIOMCP_URL", "http://localhost:8080"),
            biomcp_timeout=float(os.getenv("BIOMCP_TIMEOUT", "60.0")),
            biomcp_max_results=int(os.getenv("BIOMCP_MAX_RESULTS", "10")),
            # Retry configuration
            max_retries=int(os.getenv("MCP_MAX_RETRIES", "3")),
            retry_base_delay=float(os.getenv("MCP_RETRY_BASE_DELAY", "1.0")),
            retry_max_delay=float(os.getenv("MCP_RETRY_MAX_DELAY", "30.0")),
            retry_jitter=os.getenv("MCP_RETRY_JITTER", "true").lower() == "true",
        )

    def to_retry_config(self) -> RetryConfig:
        """Create RetryConfig from this configuration.

        Convenience method for creating RetryConfig instances
        to pass to MCP clients.

        Returns:
            RetryConfig with retry settings from this config.

        Example:
            >>> config = MCPConfig.from_env()
            >>> retry = config.to_retry_config()
            >>> retry.max_retries
            3
        """
        return RetryConfig(
            max_retries=self.max_retries,
            base_delay=self.retry_base_delay,
            max_delay=self.retry_max_delay,
            jitter=self.retry_jitter,
        )
