"""Timeout wrapper for async agent nodes.

Provides a decorator for adding timeout to agent nodes, enabling
graceful degradation when agents exceed their time budget during
parallel execution.
"""

from __future__ import annotations

import asyncio
import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Default timeout for agent nodes in seconds.
# Individual agents can override when calling @with_timeout().
DEFAULT_AGENT_TIMEOUT = 10.0


def with_timeout(
    timeout_seconds: float = DEFAULT_AGENT_TIMEOUT,
) -> Callable[..., Any]:
    """Add timeout to async agent nodes.

    If agent exceeds timeout, returns graceful degradation response
    instead of blocking the entire graph execution.

    Args:
        timeout_seconds: Maximum execution time (default: 10s).

    Returns:
        Decorator function.

    Example:
        >>> @with_timeout(timeout_seconds=10.0)
        ... async def my_agent_node(state, runtime):
        ...     return {"messages": [...], "retrieved_docs": [...]}
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"[{func.__name__}] Timeout after {timeout_seconds}s - "
                    "returning graceful degradation"
                )
                return {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": (
                                f"Agent {func.__name__} překročil časový limit "
                                f"({timeout_seconds}s)."
                            ),
                        }
                    ],
                    "retrieved_docs": [],
                    "next": "__end__",
                }

        return wrapper

    return decorator
