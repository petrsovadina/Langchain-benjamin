"""Message content extraction utilities.

Provides a single canonical function for extracting text content from
LangGraph messages, handling dict, Message object, and multimodal formats.

This module consolidates duplicated message extraction logic from:
- supervisor.py
- drug_agent.py
- guidelines_agent.py
- graph.py (route_query)
"""

from __future__ import annotations

from typing import Any


def extract_message_content(message: Any) -> str:
    """Extract text content from message (handles dict, Message, multimodal).

    Supports three message formats:
    1. Dict with "content" key: {"role": "user", "content": "text"}
    2. Message object with content attribute: HumanMessage(content="text")
    3. Multimodal list format: [{"type": "text", "text": "..."}] or ["text"]

    Args:
        message: Message object (dict, AIMessage, HumanMessage, etc.).

    Returns:
        Extracted text content as string. Empty string if extraction fails.

    Examples:
        >>> extract_message_content({"content": "Hello"})
        'Hello'
        >>> extract_message_content({"content": [{"type": "text", "text": "Hi"}]})
        'Hi'
    """
    raw_content = (
        message.get("content")
        if isinstance(message, dict)
        else getattr(message, "content", "")
    )

    # Handle string content
    if isinstance(raw_content, str):
        return raw_content

    # Handle multimodal list format
    if isinstance(raw_content, list) and raw_content:
        first_block = raw_content[0]
        if isinstance(first_block, str):
            return first_block
        elif isinstance(first_block, dict) and "text" in first_block:
            return str(first_block["text"])

    return ""
