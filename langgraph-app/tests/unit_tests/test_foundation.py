"""Unit tests for LangGraph foundation (AgentState, Context, placeholder_node).

IMPORTANT: These tests are written FIRST (Test-First Development - Principle III).
They MUST FAIL initially until implementation is complete.
"""

import pytest
from src.agent.graph import State, Context, placeholder_node


@pytest.mark.asyncio
async def test_placeholder_node_echoes_message(mock_runtime):
    """Test placeholder node echoes user message.

    Acceptance: Given a State with user message,
    When placeholder_node is invoked,
    Then it returns AI message echoing the user input.
    """
    # Arrange
    state = State(
        messages=[{"role": "user", "content": "Hello"}],
        next="placeholder"
    )

    # Act
    result = await placeholder_node(state, mock_runtime)

    # Assert
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert "Echo: Hello" in result["messages"][0]["content"]
    assert result["next"] == "__end__"


@pytest.mark.asyncio
async def test_placeholder_node_handles_empty_state(mock_runtime):
    """Test placeholder node with no messages.

    Acceptance: Given empty State,
    When placeholder_node is invoked,
    Then it returns "No input" message.
    """
    # Arrange
    state = State(messages=[], next="placeholder")

    # Act
    result = await placeholder_node(state, mock_runtime)

    # Assert
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0]["content"] == "No input"
    assert result["next"] == "__end__"


@pytest.mark.asyncio
async def test_placeholder_node_accesses_runtime_config(mock_runtime):
    """Test placeholder node can access runtime configuration.

    Acceptance: Given mock_runtime with model_name,
    When placeholder_node is invoked,
    Then it can read model_name from runtime.context.
    """
    # Arrange
    state = State(
        messages=[{"role": "user", "content": "test"}],
        next="placeholder"
    )

    # Act
    result = await placeholder_node(state, mock_runtime)

    # Assert - node should execute without error (validates runtime access)
    assert result is not None
    # Note: Actual model usage will be in future features
