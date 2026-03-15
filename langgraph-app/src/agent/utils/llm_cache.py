"""LLM instance cache for ChatAnthropic reuse.

Avoids creating new ChatAnthropic instances on every request
when model parameters are identical (~100ms savings per call).
"""

from typing import Any

from langchain_anthropic import ChatAnthropic

_CacheKey = tuple[str, float, int, int | None]
_llm_cache: dict[_CacheKey, ChatAnthropic] = {}


def get_llm(
    model_name: str,
    temperature: float = 0.0,
    timeout: int = 60,
    max_tokens: int | None = None,
) -> ChatAnthropic:
    """Get or create a cached ChatAnthropic instance.

    Args:
        model_name: Anthropic model identifier.
        temperature: Sampling temperature.
        timeout: Request timeout in seconds.
        max_tokens: Optional max tokens for response.

    Returns:
        Cached or new ChatAnthropic instance.
    """
    key = (model_name, temperature, timeout, max_tokens)
    if key not in _llm_cache:
        kwargs: dict[str, Any] = {
            "model": model_name,
            "temperature": temperature,
            "timeout": timeout,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        _llm_cache[key] = ChatAnthropic(**kwargs)
    return _llm_cache[key]
