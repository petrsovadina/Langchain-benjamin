"""SÚKL MCP Client adapter - Czech pharmaceutical database access.

Implements IMCPClient for SÚKL-mcp server using JSON-RPC protocol.
Server: https://sukl-mcp-ts.vercel.app/mcp

Available tools (MCP JSON-RPC):
- search-medicine: Search drugs by name (fuzzy matching)
- get-medicine-details: Get detailed drug info by SÚKL code
- search-by-atc: Search by ATC code (NOTE: server tool is get-atc-info)
- get-reimbursement: Get pricing/reimbursement info
- check-availability: Check drug availability/distribution status
- get-pil-content: Patient Information Leaflet
- get-spc-content: Summary of Product Characteristics
- find-pharmacies: Search pharmacies by city/postal code
- batch-check-availability: Batch availability check

Updated 2026-02-09: Rewrote from REST POST /tools/{name} to JSON-RPC envelope.
Updated 2026-02-11: Security hardening (size limits, thread-safe IDs, context manager).
"""

from __future__ import annotations

import itertools
import json
import logging
import os
import re
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

# Safety limits for content parsing
MAX_CONTENT_SIZE = 1_000_000  # 1 MB max total text content
MAX_TEXT_LENGTH = 100_000  # 100 KB max for text parsing

# JSON-RPC headers (shared across all requests)
_RPC_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

# Tool name mapping: internal name → MCP server tool name
TOOL_NAME_MAP = {
    "search_drugs": "search-medicine",
    "get_drug_details": "get-medicine-details",
    "search_by_atc": "get-atc-info",
    "get_interactions": "get-medicine-details",  # No dedicated interactions tool
    "search_side_effects": "get-medicine-details",
    "get_pricing_info": "get-reimbursement",
    "search_by_ingredient": "search-medicine",
    "validate_prescription": "search-medicine",  # No dedicated validation tool
    "get_reimbursement": "get-reimbursement",
    "check_availability": "check-availability",
    "get_pil": "get-pil-content",
    "get_spc": "get-spc-content",
    "find_pharmacies": "find-pharmacies",
}

# Parameter mapping: internal param names → MCP server param names
PARAM_MAP = {
    "search-medicine": {"query": "query", "limit": "limit"},
    "get-medicine-details": {"registration_number": "sukl_code"},
    "get-atc-info": {"atc_code": "code"},
    "get-reimbursement": {"registration_number": "sukl_code"},
    "check-availability": {"registration_number": "sukl_code", "include_alternatives": None},
    "get-pil-content": {"registration_number": "sukl_code"},
    "get-spc-content": {"registration_number": "sukl_code"},
    "find-pharmacies": {"city": "city", "postal_code": "postalCode"},
}

# ReDoS-safe pattern: line-anchored, no backtracking ambiguity
_DRUG_LINE_PATTERN = re.compile(r'^\d+\.\s+([^(]+)\s+\((\d{4,8})\)\s*-\s*(.+)$')


class DrugSearchResult(BaseModel):
    """Schema for search_drugs response."""
    name: str
    atc_code: str = ""
    registration_number: str = ""
    manufacturer: str | None = None


class SUKLMCPClient(IMCPClient):
    """Adapter: SÚKL-mcp server client using JSON-RPC protocol.

    Provides access to Czech pharmaceutical database with 68,000+ drugs.

    Note: This client uses JSON-RPC protocol (tools/call method) because
    the SÚKL-mcp server (sukl-mcp-ts.vercel.app) implements the MCP
    Streamable HTTP transport. BioMCPClient uses REST because its server
    exposes a traditional REST API. The protocol difference is intentional.

    Supports async context manager for safe resource cleanup:
        async with SUKLMCPClient() as client:
            response = await client.call_tool("search_drugs", {"query": "aspirin"})

    Example:
        >>> client = SUKLMCPClient()
        >>> response = await client.call_tool("search_drugs", {"query": "aspirin"})
        >>> print(response.data)
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        retry_strategy: IRetryStrategy | None = None,
        default_retry_config: RetryConfig | None = None,
    ):
        self.base_url = (base_url or os.getenv(
            "SUKL_MCP_URL", "http://localhost:3000"
        )).rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retry_strategy = retry_strategy
        self.default_retry_config = default_retry_config or RetryConfig()
        self._session: aiohttp.ClientSession | None = None
        self._id_counter = itertools.count(1)

        logger.info(f"[SUKLMCPClient] Initialized with base_url={self.base_url}")

    async def __aenter__(self) -> SUKLMCPClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        await self.close()

    def _next_id(self) -> int:
        """Thread-safe request ID generator."""
        return next(self._id_counter)

    def _build_rpc_request(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build JSON-RPC 2.0 request envelope."""
        request: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._next_id(),
        }
        if params is not None:
            request["params"] = params
        return request

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    def _map_tool_and_params(
        self, tool_name: str, parameters: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Map internal tool/param names to MCP server names."""
        mcp_tool = TOOL_NAME_MAP.get(tool_name, tool_name)
        param_mapping = PARAM_MAP.get(mcp_tool, {})

        mapped_params = {}
        for internal_key, value in parameters.items():
            if internal_key in param_mapping:
                mcp_key = param_mapping[internal_key]
                # Explicitly mapped to None => skip this parameter
                if mcp_key is not None:
                    mapped_params[mcp_key] = value
            else:
                # No mapping defined => pass parameter through unchanged
                mapped_params[internal_key] = value

        return mcp_tool, mapped_params

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        retry_config: RetryConfig | None = None,
    ) -> MCPResponse:
        """Call SÚKL MCP tool via JSON-RPC protocol.

        Args:
            tool_name: Tool identifier (internal name, auto-mapped to MCP name).
            parameters: Tool parameters (internal names, auto-mapped).
            retry_config: Override default retry config.

        Returns:
            MCPResponse with success/failure and data.
        """
        config = retry_config or self.default_retry_config

        async def _execute() -> MCPResponse:
            session = await self._get_session()

            # Map tool and parameter names
            mcp_tool, mcp_params = self._map_tool_and_params(tool_name, parameters)

            # Build JSON-RPC envelope
            payload = self._build_rpc_request("tools/call", {
                "name": mcp_tool,
                "arguments": mcp_params,
            })

            start_time = datetime.now()

            try:
                logger.debug(
                    f"[SUKLMCPClient] JSON-RPC call: {mcp_tool} with {mcp_params}"
                )

                async with session.post(
                    self.base_url,
                    json=payload,
                    headers=_RPC_HEADERS,
                ) as response:
                    latency_ms = int(
                        (datetime.now() - start_time).total_seconds() * 1000
                    )

                    if response.status >= 500:
                        error_text = await response.text()
                        raise MCPServerError(
                            f"SÚKL server error: {response.status} - {error_text}",
                            status_code=response.status,
                        )

                    if response.status == 429:
                        retry_after = response.headers.get("Retry-After", "60")
                        raise MCPTimeoutError(
                            f"Rate limited, retry after {retry_after}s",
                            server_url=self.base_url,
                        )

                    if response.status >= 400:
                        error_text = await response.text()
                        return MCPResponse(
                            success=False,
                            error=f"HTTP {response.status}: {error_text}",
                            metadata={"latency_ms": latency_ms},
                        )

                    # Parse JSON-RPC response
                    rpc_response = await response.json()

                    # Check for JSON-RPC error
                    if "error" in rpc_response:
                        rpc_error = rpc_response["error"]
                        return MCPResponse(
                            success=False,
                            error=f"RPC error {rpc_error.get('code')}: {rpc_error.get('message')}",
                            metadata={"latency_ms": latency_ms},
                        )

                    # Extract content from MCP result
                    result = rpc_response.get("result", {})
                    content = result.get("content", [])

                    # Parse text content blocks
                    parsed_data = self._parse_content(content)

                    return MCPResponse(
                        success=True,
                        data=parsed_data,
                        metadata={
                            "latency_ms": latency_ms,
                            "server_url": self.base_url,
                            "tool_name": mcp_tool,
                            "original_tool": tool_name,
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

        if self.retry_strategy:
            result = await self.retry_strategy.execute_with_retry(_execute, config)
            return cast(MCPResponse, result)
        else:
            return await _execute()

    def _parse_content(self, content: list[dict[str, Any]]) -> dict[str, Any]:
        """Parse MCP content blocks into structured data.

        The SÚKL MCP server returns text content that may be:
        - Formatted human-readable text (search results, details)
        - JSON strings (structured data)

        We try JSON first, fall back to raw text.
        Enforces size limits to prevent memory exhaustion from untrusted servers.
        """
        texts: list[str] = []
        total_size = 0

        for block in content:
            if block.get("type") == "text":
                text = block.get("text", "")
                total_size += len(text)
                if total_size > MAX_CONTENT_SIZE:
                    logger.warning(
                        "[SUKLMCPClient] Content exceeds %d bytes, truncating",
                        MAX_CONTENT_SIZE,
                    )
                    break
                texts.append(text)

        combined = "\n".join(texts)

        # Try to parse as JSON
        try:
            parsed = json.loads(combined)
            return {"drugs": parsed}
        except (json.JSONDecodeError, ValueError, RecursionError):
            pass

        # Parse formatted text response into structured data
        return self._parse_text_response(combined)

    def _parse_text_response(self, text: str) -> dict[str, Any]:
        """Parse human-readable text response into structured data.

        Uses line-anchored regex to prevent ReDoS.
        """
        if len(text) > MAX_TEXT_LENGTH:
            logger.warning(
                "[SUKLMCPClient] Text response too long (%d chars), truncating",
                len(text),
            )
            text = text[:MAX_TEXT_LENGTH]

        drugs: list[dict[str, str]] = []
        for line in text.split('\n'):
            match = _DRUG_LINE_PATTERN.match(line.strip())
            if match:
                name, code, ingredient = match.groups()
                drugs.append({
                    "name": name.strip(),
                    "registration_number": code.strip(),
                    "atc_code": "",
                    "active_ingredient": ingredient.strip(),
                })

        if drugs:
            return {"drugs": drugs, "raw_text": text}

        # Return raw text if no structured parsing possible
        return {"raw_text": text, "drugs": []}

    async def health_check(self, timeout: float = 5.0) -> MCPHealthStatus:
        """Check SÚKL server health via JSON-RPC tools/list."""
        try:
            session = await self._get_session()
            start_time = datetime.now()

            payload = self._build_rpc_request("tools/list")

            async with session.post(
                self.base_url,
                json=payload,
                headers=_RPC_HEADERS,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)

                if response.status == 200:
                    data = await response.json()
                    tools = data.get("result", {}).get("tools", [])
                    return MCPHealthStatus(
                        status="healthy",
                        latency_ms=latency_ms,
                        tools_count=len(tools),
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
        """List available SÚKL MCP tools via JSON-RPC."""
        try:
            session = await self._get_session()
            payload = self._build_rpc_request("tools/list")
            async with session.post(
                self.base_url,
                json=payload,
                headers=_RPC_HEADERS,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tools = data.get("result", {}).get("tools", [])
                    return [
                        MCPToolMetadata(
                            name=t["name"],
                            description=t.get("description", ""),
                            parameters=t.get("inputSchema", {}).get("properties", {}),
                            returns={},
                        )
                        for t in tools
                    ]
        except Exception as e:
            logger.warning(f"[SUKLMCPClient] Failed to list tools: {e}")

        # Fallback: hardcoded list
        return [
            MCPToolMetadata(name="search-medicine", description="Search drugs by name", parameters={"query": "string"}, returns={}),
            MCPToolMetadata(name="get-medicine-details", description="Get drug details by SÚKL code", parameters={"suklCode": "string"}, returns={}),
            MCPToolMetadata(name="get-atc-info", description="Search by ATC code", parameters={"code": "string"}, returns={}),
            MCPToolMetadata(name="get-reimbursement", description="Get pricing/reimbursement", parameters={"suklCode": "string"}, returns={}),
            MCPToolMetadata(name="check-availability", description="Check drug availability", parameters={"suklCode": "string"}, returns={}),
            MCPToolMetadata(name="get-pil-content", description="Patient Information Leaflet", parameters={"suklCode": "string"}, returns={}),
            MCPToolMetadata(name="get-spc-content", description="Summary of Product Characteristics", parameters={"suklCode": "string"}, returns={}),
            MCPToolMetadata(name="find-pharmacies", description="Search pharmacies", parameters={"city": "string"}, returns={}),
        ]

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            logger.info("[SUKLMCPClient] Session closed")

    # High-level typed helpers

    async def search_drugs(self, query: str) -> list[DrugSearchResult]:
        """Search drugs by name (typed helper)."""
        response = await self.call_tool("search_drugs", {"query": query})

        if not response.success:
            raise MCPValidationError(f"Drug search failed: {response.error}")

        try:
            return [
                DrugSearchResult(
                    name=drug.get("name", ""),
                    atc_code=drug.get("atc_code", ""),
                    registration_number=drug.get("registration_number", ""),
                    manufacturer=drug.get("manufacturer"),
                )
                for drug in response.data.get("drugs", [])
            ]
        except ValidationError as e:
            raise MCPValidationError(
                "Invalid drug search response", validation_errors=e.errors()
            ) from e
