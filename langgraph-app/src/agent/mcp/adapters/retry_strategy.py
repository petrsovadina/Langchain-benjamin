"""Retry strategy adapter using Tenacity library.

Implements IRetryStrategy with exponential backoff and jitter
for resilient MCP operations.

Following Constitution:
- Principle II (Type Safety): Full type hints
- Principle IV (Observability): Logging of retry attempts
- Principle V (Modular): Separated retry logic from MCP clients
"""

from __future__ import annotations

import logging
import random
from typing import Any, Awaitable, Callable, Union

from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from tenacity.wait import wait_base

from ..domain.entities import RetryConfig
from ..domain.exceptions import MCPConnectionError, MCPServerError, MCPTimeoutError
from ..domain.ports import IRetryStrategy

logger = logging.getLogger(__name__)


class TenacityRetryStrategy(IRetryStrategy):
    """Adapter: Retry strategy using Tenacity.

    Implements exponential backoff with optional jitter for:
    - MCPConnectionError (transient network issues)
    - MCPTimeoutError (including rate limiting 429)
    - MCPServerError (5xx errors)

    Does NOT retry:
    - MCPValidationError (client-side error, permanent)
    - 4xx errors except 429 (client error, won't fix)
    - Generic exceptions (unexpected errors)

    Example:
        >>> strategy = TenacityRetryStrategy()
        >>> config = RetryConfig(max_retries=3, base_delay=1.0)
        >>> result = await strategy.execute_with_retry(my_operation, config)
    """

    def __init__(self) -> None:
        """Initialize retry strategy."""
        logger.info("[TenacityRetryStrategy] Initialized")

    async def execute_with_retry(
        self,
        operation: Union[
            Callable[[], Any],
            Callable[[], Awaitable[Any]],
        ],
        config: RetryConfig,
    ) -> Any:
        """Execute async operation with exponential backoff.

        Args:
            operation: Async callable to retry.
            config: Retry configuration.

        Returns:
            Operation result.

        Raises:
            Original exception after max_retries exhausted.
        """
        # Build Tenacity retry decorator dynamically
        retry_decorator = retry(
            stop=stop_after_attempt(config.max_retries + 1),  # +1 for initial attempt
            wait=self._build_wait_strategy(config),
            retry=retry_if_exception_type(
                (
                    MCPConnectionError,
                    MCPTimeoutError,
                    MCPServerError,
                )
            ),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )

        # Apply decorator to operation
        retryable_operation = retry_decorator(operation)

        try:
            return await retryable_operation()
        except RetryError as e:
            # Tenacity wraps exception, unwrap for clean error
            if e.last_attempt.exception() is not None:
                raise e.last_attempt.exception() from e
            raise

    def _build_wait_strategy(
        self, config: RetryConfig
    ) -> Union[wait_base, Callable[[Any], float]]:
        """Build Tenacity wait strategy with optional jitter.

        Args:
            config: RetryConfig with base_delay, max_delay, jitter, exponential_base.

        Returns:
            Tenacity wait strategy function.
        """
        base_wait = wait_exponential(
            multiplier=config.base_delay,
            max=config.max_delay,
            exp_base=config.exponential_base,
        )

        if config.jitter:
            # Add jitter: random ±20% of calculated delay
            def wait_with_jitter(retry_state: Any) -> float:
                delay = base_wait(retry_state)
                # Ensure delay is a float
                delay_float = float(delay) if delay is not None else 0.0
                # Add ±20% jitter
                jitter_amount = delay_float * 0.2 * (random.random() * 2 - 1)
                return max(0.0, delay_float + jitter_amount)

            return wait_with_jitter
        else:
            return base_wait
