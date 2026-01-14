"""Unit tests for MCP domain exceptions."""

from __future__ import annotations

import pytest

from agent.mcp.domain.exceptions import (
    MCPError,
    MCPConnectionError,
    MCPTimeoutError,
    MCPValidationError,
    MCPServerError
)


class TestMCPError:
    """Test base MCPError exception."""

    def test_mcp_error_with_message(self):
        """Test MCPError creation with message."""
        error = MCPError("Base error")

        assert str(error) == "Base error"
        assert error.message == "Base error"
        assert error.server_url is None

    def test_mcp_error_with_server_url(self):
        """Test MCPError with server_url."""
        error = MCPError("Error", server_url="http://localhost:3000")

        assert error.message == "Error"
        assert error.server_url == "http://localhost:3000"

    def test_mcp_error_inheritance(self):
        """Test MCPError inherits from Exception."""
        error = MCPError("Test")

        assert isinstance(error, Exception)


class TestMCPConnectionError:
    """Test MCPConnectionError exception."""

    def test_connection_error_creation(self):
        """Test MCPConnectionError with server_url."""
        error = MCPConnectionError(
            "Cannot connect to SÚKL server",
            server_url="http://localhost:3000"
        )

        assert str(error) == "Cannot connect to SÚKL server"
        assert error.message == "Cannot connect to SÚKL server"
        assert error.server_url == "http://localhost:3000"

    def test_connection_error_inherits_from_mcp_error(self):
        """Test MCPConnectionError inherits from MCPError."""
        error = MCPConnectionError("Test")

        assert isinstance(error, MCPError)
        assert isinstance(error, Exception)


class TestMCPTimeoutError:
    """Test MCPTimeoutError exception."""

    def test_timeout_error_creation(self):
        """Test MCPTimeoutError with timeout details."""
        error = MCPTimeoutError(
            "Request timeout after 30s",
            server_url="http://localhost:8080"
        )

        assert str(error) == "Request timeout after 30s"
        assert error.server_url == "http://localhost:8080"

    def test_timeout_error_inherits_from_mcp_error(self):
        """Test MCPTimeoutError inherits from MCPError."""
        error = MCPTimeoutError("Test")

        assert isinstance(error, MCPError)


class TestMCPValidationError:
    """Test MCPValidationError exception."""

    def test_validation_error_without_validation_errors(self):
        """Test MCPValidationError with message only."""
        error = MCPValidationError("Invalid response schema")

        assert str(error) == "Invalid response schema"
        assert error.message == "Invalid response schema"
        assert error.validation_errors == []

    def test_validation_error_with_validation_errors_list(self):
        """Test MCPValidationError with Pydantic-style errors."""
        validation_errors = [
            {"loc": ["drugs", 0, "name"], "msg": "field required"},
            {"loc": ["drugs", 0, "atc_code"], "msg": "field required"}
        ]

        error = MCPValidationError(
            "Invalid SÚKL response",
            validation_errors=validation_errors
        )

        assert error.message == "Invalid SÚKL response"
        assert len(error.validation_errors) == 2
        assert error.validation_errors[0]["loc"] == ["drugs", 0, "name"]

    def test_validation_error_inherits_from_mcp_error(self):
        """Test MCPValidationError inherits from MCPError."""
        error = MCPValidationError("Test")

        assert isinstance(error, MCPError)


class TestMCPServerError:
    """Test MCPServerError exception."""

    def test_server_error_with_status_code(self):
        """Test MCPServerError with HTTP status code."""
        error = MCPServerError("Internal Server Error", status_code=500)

        assert str(error) == "Internal Server Error"
        assert error.status_code == 500

    def test_server_error_503(self):
        """Test MCPServerError for service unavailable."""
        error = MCPServerError("Service unavailable", status_code=503)

        assert error.status_code == 503

    def test_server_error_inherits_from_mcp_error(self):
        """Test MCPServerError inherits from MCPError."""
        error = MCPServerError("Test", status_code=500)

        assert isinstance(error, MCPError)


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_mcp_error(self):
        """Test all MCP exceptions inherit from MCPError."""
        exceptions = [
            MCPConnectionError("test"),
            MCPTimeoutError("test"),
            MCPValidationError("test"),
            MCPServerError("test", status_code=500)
        ]

        for exc in exceptions:
            assert isinstance(exc, MCPError)
            assert isinstance(exc, Exception)

    def test_exception_can_be_raised_and_caught(self):
        """Test exceptions can be raised and caught normally."""
        with pytest.raises(MCPConnectionError, match="Connection failed"):
            raise MCPConnectionError("Connection failed")

        with pytest.raises(MCPError):
            raise MCPTimeoutError("Timeout")
