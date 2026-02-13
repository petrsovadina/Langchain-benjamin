"""Integration tests for LangGraph foundation (graph execution).

IMPORTANT: These tests are written FIRST (Test-First Development - Principle III).
They MUST FAIL initially until graph implementation is complete.
"""

import pytest


@pytest.mark.asyncio
async def test_graph_invocation_returns_state(test_graph):
    """Test graph can be invoked and returns valid state.

    Acceptance: Given compiled graph,
    When invoked with input state and context,
    Then returns state with user + AI messages.
    """
    # Arrange
    input_state = {"messages": [{"role": "user", "content": "test"}]}
    context = {"model_name": "test-model", "temperature": 0.0}

    # Act
    result = await test_graph.ainvoke(input_state, config={"configurable": context})

    # Assert
    assert "messages" in result
    assert len(result["messages"]) == 2  # User + AI message
    assert result["messages"][0].content == "test"
    assert "Echo: test" in result["messages"][1].content


@pytest.mark.asyncio
async def test_graph_renders_correctly(test_graph):
    """Test graph structure is valid for visualization.

    Acceptance: Given compiled graph,
    When get_graph() is called,
    Then returns graph dict with general_agent node.
    """
    # Act
    graph_dict = test_graph.get_graph().to_json()

    # Assert
    assert "nodes" in graph_dict
    node_ids = [n["id"] for n in graph_dict["nodes"]]
    assert "general_agent" in node_ids
    assert "__start__" in node_ids
    assert "__end__" in node_ids


@pytest.mark.asyncio
async def test_graph_handles_empty_messages(test_graph):
    """Test graph handles edge case of empty messages.

    Acceptance: Given empty messages list,
    When graph is invoked,
    Then returns "No input" response.
    """
    # Arrange
    input_state = {"messages": []}
    context = {"model_name": "test-model", "temperature": 0.0}

    # Act
    result = await test_graph.ainvoke(input_state, config={"configurable": context})

    # Assert
    assert "messages" in result
    assert len(result["messages"]) == 1  # AI message only
    assert result["messages"][0].content == "No input"


@pytest.mark.asyncio
async def test_graph_execution_performance(test_graph):
    """Test graph executes within performance target.

    Acceptance: Given graph invocation,
    When measured,
    Then completes in <100ms (NFR-003: node <50ms + overhead).
    """
    import time

    # Arrange
    input_state = {"messages": [{"role": "user", "content": "performance test"}]}
    context = {"model_name": "test-model", "temperature": 0.0}

    # Act
    start = time.time()
    result = await test_graph.ainvoke(input_state, config={"configurable": context})
    duration_ms = (time.time() - start) * 1000

    # Assert
    assert result is not None
    assert duration_ms < 100, f"Graph execution took {duration_ms}ms (target: <100ms)"
