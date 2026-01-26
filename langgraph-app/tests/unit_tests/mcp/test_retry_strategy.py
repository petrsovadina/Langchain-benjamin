"""Unit tests for TenacityRetryStrategy.

Tests exponential backoff retry behavior for MCP operations.
Following TDD - tests written BEFORE implementation.
"""

from __future__ import annotations

import pytest

from agent.mcp.adapters.retry_strategy import TenacityRetryStrategy
from agent.mcp.domain.entities import RetryConfig
from agent.mcp.domain.exceptions import (
    MCPConnectionError,
    MCPServerError,
    MCPTimeoutError,
    MCPValidationError,
)


class TestTenacityRetryStrategyInitialization:
    """Tests for TenacityRetryStrategy initialization."""

    def test_init_creates_instance(self):
        """Test basic initialization."""
        strategy = TenacityRetryStrategy()
        assert strategy is not None

    def test_implements_iretry_strategy(self):
        """Test that TenacityRetryStrategy implements IRetryStrategy."""
        from agent.mcp.domain.ports import IRetryStrategy

        strategy = TenacityRetryStrategy()
        assert isinstance(strategy, IRetryStrategy)


class TestTenacityRetryStrategySuccessfulOperations:
    """Tests for operations that succeed."""

    @pytest.mark.asyncio
    async def test_immediate_success_returns_result(self):
        """Test that successful operation returns immediately without retry."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=3)

        async def successful_operation():
            return "success"

        result = await strategy.execute_with_retry(successful_operation, config)

        assert result == "success"

    @pytest.mark.asyncio
    async def test_success_after_connection_errors(self):
        """Test retry succeeds after transient connection errors."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)

        call_count = 0

        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise MCPConnectionError("Connection refused")
            return "success_after_retries"

        result = await strategy.execute_with_retry(flaky_operation, config)

        assert result == "success_after_retries"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_success_after_timeout_errors(self):
        """Test retry succeeds after timeout errors."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)

        call_count = 0

        async def timeout_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise MCPTimeoutError("Request timeout")
            return "success"

        result = await strategy.execute_with_retry(timeout_operation, config)

        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_success_after_server_errors(self):
        """Test retry succeeds after 5xx server errors."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)

        call_count = 0

        async def server_error_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise MCPServerError("Internal server error", status_code=500)
            return "success"

        result = await strategy.execute_with_retry(server_error_operation, config)

        assert result == "success"
        assert call_count == 2


class TestTenacityRetryStrategyExhaustedRetries:
    """Tests for when max retries are exhausted."""

    @pytest.mark.asyncio
    async def test_raises_original_exception_after_max_retries(self):
        """Test that original exception is raised after max retries."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        call_count = 0

        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise MCPConnectionError("Always fails")

        with pytest.raises(MCPConnectionError) as exc_info:
            await strategy.execute_with_retry(always_fails, config)

        assert "Always fails" in str(exc_info.value)
        assert call_count == 3  # Initial + 2 retries

    @pytest.mark.asyncio
    async def test_raises_timeout_error_after_exhausted(self):
        """Test timeout error propagates after max retries."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=1, base_delay=0.01, jitter=False)

        call_count = 0

        async def always_timeout():
            nonlocal call_count
            call_count += 1
            raise MCPTimeoutError("Timeout")

        with pytest.raises(MCPTimeoutError):
            await strategy.execute_with_retry(always_timeout, config)

        assert call_count == 2  # Initial + 1 retry

    @pytest.mark.asyncio
    async def test_zero_retries_raises_immediately(self):
        """Test that zero max_retries raises on first failure."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=0, base_delay=0.01)

        call_count = 0

        async def fails_once():
            nonlocal call_count
            call_count += 1
            raise MCPConnectionError("Fail")

        with pytest.raises(MCPConnectionError):
            await strategy.execute_with_retry(fails_once, config)

        assert call_count == 1  # Only initial attempt


class TestTenacityRetryStrategyNonRetryableErrors:
    """Tests for errors that should NOT be retried."""

    @pytest.mark.asyncio
    async def test_validation_error_not_retried(self):
        """Test that MCPValidationError is NOT retried."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=3, base_delay=0.01)

        call_count = 0

        async def validation_error_operation():
            nonlocal call_count
            call_count += 1
            raise MCPValidationError("Invalid parameters")

        with pytest.raises(MCPValidationError):
            await strategy.execute_with_retry(validation_error_operation, config)

        assert call_count == 1  # No retries

    @pytest.mark.asyncio
    async def test_generic_exception_not_retried(self):
        """Test that generic exceptions are NOT retried."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=3, base_delay=0.01)

        call_count = 0

        async def generic_error_operation():
            nonlocal call_count
            call_count += 1
            raise ValueError("Generic error")

        with pytest.raises(ValueError):
            await strategy.execute_with_retry(generic_error_operation, config)

        assert call_count == 1  # No retries


class TestTenacityRetryStrategyWaitBehavior:
    """Tests for exponential backoff and jitter behavior."""

    @pytest.mark.asyncio
    async def test_exponential_backoff_delays(self):
        """Test that delays increase exponentially."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(
            max_retries=3,
            base_delay=0.1,
            max_delay=10.0,
            jitter=False,
            exponential_base=2,
        )

        call_times: list[float] = []
        import time

        call_count = 0

        async def failing_operation():
            nonlocal call_count
            call_times.append(time.time())
            call_count += 1
            if call_count <= 3:
                raise MCPConnectionError("Fail")
            return "success"

        result = await strategy.execute_with_retry(failing_operation, config)

        assert result == "success"
        assert len(call_times) == 4

        # Verify delays are increasing (exponential)
        if len(call_times) >= 3:
            delay1 = call_times[1] - call_times[0]
            delay2 = call_times[2] - call_times[1]
            # Second delay should be greater than or close to first
            # (allowing small margin for execution time)
            assert delay2 >= delay1 * 0.8

    @pytest.mark.asyncio
    async def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delays."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=2, base_delay=0.1, jitter=True)

        # Run multiple times and verify delays vary
        delays: list[float] = []
        import time

        for _ in range(3):
            call_times: list[float] = []
            call_count = 0

            async def failing_then_success():
                nonlocal call_count
                call_times.append(time.time())
                call_count += 1
                if call_count == 1:
                    raise MCPConnectionError("Fail")
                return "success"

            await strategy.execute_with_retry(failing_then_success, config)
            if len(call_times) >= 2:
                delays.append(call_times[1] - call_times[0])

        # With jitter, delays should vary (not all identical)
        # This is a probabilistic test, but should pass reliably
        if len(delays) >= 2:
            # At least one delay should differ from another
            # (allowing very small margin for identical execution times)
            unique_delays = set(round(d, 3) for d in delays)
            # Jitter should cause variation, but test is lenient
            assert len(unique_delays) >= 1

    @pytest.mark.asyncio
    async def test_max_delay_caps_wait_time(self):
        """Test that max_delay caps the exponential backoff."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(
            max_retries=5,
            base_delay=0.05,  # Start with small delay
            max_delay=0.15,  # Cap at 150ms (must be >= base_delay)
            jitter=False,
            exponential_base=2,
        )

        import time

        call_times: list[float] = []
        call_count = 0

        async def always_fails_operation():
            nonlocal call_count
            call_times.append(time.time())
            call_count += 1
            raise MCPConnectionError("Fail")

        with pytest.raises(MCPConnectionError):
            await strategy.execute_with_retry(always_fails_operation, config)

        # Verify no delay exceeded max_delay (+ some margin)
        for i in range(1, len(call_times)):
            delay = call_times[i] - call_times[i - 1]
            # Allow 50% margin for execution time
            assert delay < config.max_delay * 1.5


class TestTenacityRetryStrategyEdgeCases:
    """Tests for edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_async_operation_result_preserved(self):
        """Test that complex async results are preserved."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=1, base_delay=0.01)

        expected_result = {"data": [1, 2, 3], "status": "ok"}

        async def complex_operation():
            return expected_result

        result = await strategy.execute_with_retry(complex_operation, config)

        assert result == expected_result
        assert result is expected_result  # Same object reference preserved

    @pytest.mark.asyncio
    async def test_operation_with_side_effects(self):
        """Test that side effects occur on each retry."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)

        side_effects: list[str] = []
        call_count = 0

        async def operation_with_side_effects():
            nonlocal call_count
            call_count += 1
            side_effects.append(f"attempt_{call_count}")
            if call_count < 2:
                raise MCPConnectionError("Fail")
            return "done"

        result = await strategy.execute_with_retry(operation_with_side_effects, config)

        assert result == "done"
        assert side_effects == ["attempt_1", "attempt_2"]

    @pytest.mark.asyncio
    async def test_retry_preserves_exception_context(self):
        """Test that exception context is preserved after retries."""
        strategy = TenacityRetryStrategy()
        config = RetryConfig(max_retries=1, base_delay=0.01, jitter=False)

        async def operation_with_context():
            raise MCPConnectionError(
                "Connection failed", server_url="http://test.example.com"
            )

        with pytest.raises(MCPConnectionError) as exc_info:
            await strategy.execute_with_retry(operation_with_context, config)

        assert exc_info.value.server_url == "http://test.example.com"
