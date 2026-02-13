"""Unit tests for LangGraph foundation (AgentState, Context, general_agent_node).

IMPORTANT: These tests are written FIRST (Test-First Development - Principle III).
They MUST FAIL initially until implementation is complete.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.graph import State, general_agent_node


@pytest.mark.asyncio
async def test_general_agent_node_responds_to_message(mock_runtime):
    """Test general_agent node responds to user message via LLM.

    Acceptance: Given a State with user message,
    When general_agent_node is invoked,
    Then it returns AI message with LLM response.
    """
    state = State(messages=[{"role": "user", "content": "Hello"}], next="general_agent")

    mock_llm_response = MagicMock()
    mock_llm_response.content = "Test response"

    with patch("langchain_anthropic.ChatAnthropic") as mock_chat_cls:
        mock_chat_instance = MagicMock()
        mock_chat_instance.ainvoke = AsyncMock(return_value=mock_llm_response)
        mock_chat_cls.return_value = mock_chat_instance

        result = await general_agent_node(state, mock_runtime)

    assert "messages" in result
    assert len(result["messages"]) == 1
    assert "Test response" in result["messages"][0]["content"]
    assert result["next"] == "__end__"


@pytest.mark.asyncio
async def test_general_agent_node_handles_empty_state(mock_runtime):
    """Test general_agent node with no messages.

    Acceptance: Given empty State,
    When general_agent_node is invoked,
    Then it returns fallback message.
    """
    state = State(messages=[], next="general_agent")

    result = await general_agent_node(state, mock_runtime)

    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0]["content"] == "Nebyl zadán žádný dotaz."
    assert result["next"] == "__end__"


@pytest.mark.asyncio
async def test_general_agent_node_accesses_runtime_config(mock_runtime):
    """Test general_agent node can access runtime configuration.

    Acceptance: Given mock_runtime with model_name,
    When general_agent_node is invoked,
    Then it executes successfully with LLM call.
    """
    state = State(messages=[{"role": "user", "content": "test"}], next="general_agent")

    mock_llm_response = MagicMock()
    mock_llm_response.content = "Test response"

    with patch("langchain_anthropic.ChatAnthropic") as mock_chat_cls:
        mock_chat_instance = MagicMock()
        mock_chat_instance.ainvoke = AsyncMock(return_value=mock_llm_response)
        mock_chat_cls.return_value = mock_chat_instance

        result = await general_agent_node(state, mock_runtime)

    assert result is not None
    assert "messages" in result
