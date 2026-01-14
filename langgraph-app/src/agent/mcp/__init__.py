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
    sukl = SUKLMCPClient(base_url=config.sukl_url)

    drugs = await sukl.search_drugs("aspirin")
"""

__version__ = "0.1.0"

# Public API will be populated as implementation progresses
__all__ = []
