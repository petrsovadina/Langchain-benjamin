"""MCP Infrastructure for Czech MedAI.

This package provides Model Context Protocol (MCP) client implementations
for accessing external data sources:
- SÚKL-mcp: Czech pharmaceutical database (68k+ drugs)
- BioMCP: Biomedical research databases (PubMed, Clinical Trials, etc.)

Architecture: Hexagonal (Ports & Adapters)
- domain/: Pure Python entities and interfaces
- adapters/: MCP client implementations

Usage:
    from agent.mcp import SUKLMCPClient, BioMCPClient, MCPConfig

    config = MCPConfig.from_env()
    sukl = SUKLMCPClient(
        base_url=config.sukl_url,
        timeout=config.sukl_timeout,
        default_retry_config=config.to_retry_config()
    )

    drugs = await sukl.search_drugs("aspirin")
"""

__version__ = "0.1.0"

# Domain entities
from .adapters.biomcp_client import BioMCPClient
from .adapters.retry_strategy import TenacityRetryStrategy

# Adapters (implementations)
from .adapters.sukl_client import SUKLMCPClient

# Configuration
from .config import MCPConfig
from .domain.entities import (
    MCPHealthStatus,
    MCPResponse,
    MCPToolMetadata,
    RetryConfig,
)

# Domain exceptions
from .domain.exceptions import (
    MCPConnectionError,
    MCPError,
    MCPServerError,
    MCPTimeoutError,
    MCPValidationError,
)

# Domain ports (interfaces)
from .domain.ports import IMCPClient, IRetryStrategy

__all__ = [
    # Version
    "__version__",
    # Domain entities
    "MCPResponse",
    "MCPHealthStatus",
    "RetryConfig",
    "MCPToolMetadata",
    # Domain ports
    "IMCPClient",
    "IRetryStrategy",
    # Domain exceptions
    "MCPError",
    "MCPConnectionError",
    "MCPTimeoutError",
    "MCPValidationError",
    "MCPServerError",
    # Adapters
    "SUKLMCPClient",
    "BioMCPClient",
    "TenacityRetryStrategy",
    # Configuration
    "MCPConfig",
]
