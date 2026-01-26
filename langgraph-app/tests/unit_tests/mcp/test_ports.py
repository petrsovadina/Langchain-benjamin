"""Unit tests for MCP domain ports (abstract interfaces)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from agent.mcp.domain.entities import (
    MCPHealthStatus,
    MCPResponse,
    MCPToolMetadata,
    RetryConfig,
)
from agent.mcp.domain.ports import IMCPClient, IRetryStrategy


class TestIMCPClient:
    """Test IMCPClient abstract base class."""

    def test_cannot_instantiate_imcp_client_directly(self):
        """Test IMCPClient cannot be instantiated (is ABC)."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IMCPClient()  # type: ignore

    def test_concrete_implementation_must_implement_all_methods(self):
        """Test concrete class must implement all abstract methods."""

        # Missing call_tool implementation
        class IncompleteClient(IMCPClient):
            async def health_check(self, timeout: float = 5.0) -> MCPHealthStatus:
                return MCPHealthStatus(status="healthy")

            async def list_tools(self) -> List[MCPToolMetadata]:
                return []

            async def close(self) -> None:
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteClient()  # type: ignore

    def test_complete_implementation_can_be_instantiated(self):
        """Test complete implementation of IMCPClient works."""

        class MockMCPClient(IMCPClient):
            async def call_tool(
                self,
                tool_name: str,
                parameters: Dict[str, Any],
                retry_config: Optional[RetryConfig] = None,
            ) -> MCPResponse:
                return MCPResponse(success=True, data={})

            async def health_check(self, timeout: float = 5.0) -> MCPHealthStatus:
                return MCPHealthStatus(status="healthy")

            async def list_tools(self) -> List[MCPToolMetadata]:
                return []

            async def close(self) -> None:
                pass

        # Should not raise
        client = MockMCPClient()
        assert isinstance(client, IMCPClient)

    @pytest.mark.asyncio
    async def test_mock_client_call_tool_signature(self):
        """Test call_tool method has correct signature."""

        class MockMCPClient(IMCPClient):
            async def call_tool(
                self,
                tool_name: str,
                parameters: Dict[str, Any],
                retry_config: Optional[RetryConfig] = None,
            ) -> MCPResponse:
                return MCPResponse(
                    success=True,
                    data={"tool": tool_name},
                    metadata={"params": parameters},
                )

            async def health_check(self, timeout: float = 5.0) -> MCPHealthStatus:
                return MCPHealthStatus(status="healthy")

            async def list_tools(self) -> List[MCPToolMetadata]:
                return []

            async def close(self) -> None:
                pass

        client = MockMCPClient()
        response = await client.call_tool("test_tool", {"param": "value"})

        assert response.success is True
        assert response.data["tool"] == "test_tool"

    @pytest.mark.asyncio
    async def test_mock_client_health_check_signature(self):
        """Test health_check method has correct signature."""

        class MockMCPClient(IMCPClient):
            async def call_tool(
                self,
                tool_name: str,
                parameters: Dict[str, Any],
                retry_config: Optional[RetryConfig] = None,
            ) -> MCPResponse:
                return MCPResponse(success=True, data={})

            async def health_check(self, timeout: float = 5.0) -> MCPHealthStatus:
                return MCPHealthStatus(status="healthy", latency_ms=50, tools_count=8)

            async def list_tools(self) -> List[MCPToolMetadata]:
                return []

            async def close(self) -> None:
                pass

        client = MockMCPClient()
        status = await client.health_check(timeout=3.0)

        assert status.status == "healthy"
        assert status.latency_ms == 50


class TestIRetryStrategy:
    """Test IRetryStrategy abstract base class."""

    def test_cannot_instantiate_iretry_strategy_directly(self):
        """Test IRetryStrategy cannot be instantiated (is ABC)."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IRetryStrategy()  # type: ignore

    def test_complete_retry_strategy_implementation(self):
        """Test complete implementation of IRetryStrategy works."""

        class MockRetryStrategy(IRetryStrategy):
            async def execute_with_retry(
                self, operation: Any, config: RetryConfig
            ) -> Any:
                # Just execute without retry for testing
                return await operation()

        # Should not raise
        strategy = MockRetryStrategy()
        assert isinstance(strategy, IRetryStrategy)

    @pytest.mark.asyncio
    async def test_mock_retry_strategy_execution(self):
        """Test retry strategy can execute operations."""

        class MockRetryStrategy(IRetryStrategy):
            async def execute_with_retry(
                self, operation: Any, config: RetryConfig
            ) -> Any:
                result = await operation()
                return result

        strategy = MockRetryStrategy()
        config = RetryConfig(max_retries=3)

        async def test_operation():
            return {"result": "success"}

        result = await strategy.execute_with_retry(test_operation, config)

        assert result == {"result": "success"}
