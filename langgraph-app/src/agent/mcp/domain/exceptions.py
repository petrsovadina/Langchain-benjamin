"""MCP domain exceptions - custom error types.

Hierarchy:
- MCPError (base)
  ├── MCPConnectionError (network/connection failures)
  ├── MCPTimeoutError (timeout including rate limiting)
  ├── MCPValidationError (schema/parameter validation)
  └── MCPServerError (server-side 5xx errors)
"""

from __future__ import annotations

from typing import Any, Optional


class MCPError(Exception):
    """Base exception for all MCP errors.

    All MCP-specific exceptions inherit from this class.
    Allows catching all MCP errors with single except clause.

    Attributes:
        message: Error message.
        server_url: Optional MCP server URL for context.
    """

    def __init__(self, message: str, server_url: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.server_url = server_url


class MCPConnectionError(MCPError):
    """Failed to connect to MCP server.

    Raised when:
    - Server is not reachable (connection refused)
    - DNS resolution fails
    - Network is unavailable

    Should trigger retry with exponential backoff.
    """
    pass


class MCPTimeoutError(MCPError):
    """MCP request exceeded timeout.

    Raised when:
    - Request takes longer than configured timeout
    - Rate limiting (HTTP 429) encountered

    Should trigger retry with exponential backoff.
    """
    pass


class MCPValidationError(MCPError):
    """Invalid MCP request or response.

    Raised when:
    - Request parameters fail validation
    - Response schema doesn't match expected format
    - Pydantic validation fails

    Should NOT be retried (client-side error).

    Attributes:
        message: Error message.
        validation_errors: List of Pydantic-style validation errors.
    """

    def __init__(self, message: str, validation_errors: Optional[list[Any]] = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []


class MCPServerError(MCPError):
    """MCP server returned 5xx error.

    Raised when:
    - Server returns HTTP 500 (Internal Server Error)
    - Server returns HTTP 503 (Service Unavailable)
    - Any other 5xx status code

    Should trigger retry with exponential backoff.

    Attributes:
        message: Error message.
        status_code: HTTP status code (500, 503, etc.).
    """

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code
