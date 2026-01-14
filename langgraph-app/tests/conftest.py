"""Pytest fixtures for Czech MedAI foundation tests."""

import pytest
from src.agent.graph import State, Context, graph


@pytest.fixture(scope="session")
def anyio_backend():
    """Configure asyncio backend for pytest-asyncio."""
    return "asyncio"


@pytest.fixture
def sample_state():
    """Provide a valid State instance for testing.

    Returns:
        State: Sample state with user message and default fields.
    """
    return State(
        messages=[{"role": "user", "content": "test message"}],
        next="placeholder",
        retrieved_docs=[]
    )


@pytest.fixture
def mock_runtime():
    """Provide a mock Runtime with complete context.

    Returns:
        MockRuntime: Runtime-like object with all Context fields.
    """
    class MockRuntime:
        def __init__(self):
            self.context = {
                # Core fields
                "model_name": "test-model",
                "temperature": 0.0,
                "langsmith_project": "test-project",
                "user_id": None,

                # MCP clients (None in foundation - implemented in Feature 002)
                "sukl_mcp_client": None,
                "biomcp_client": None,

                # Conversation persistence (None - implemented in Feature 013)
                "conversation_context": None,

                # Workflow mode (default: quick)
                "mode": "quick"
            }

    return MockRuntime()


@pytest.fixture
def test_graph():
    """Provide the compiled graph for integration tests.

    Returns:
        CompiledGraph: Czech MedAI Foundation graph instance.
    """
    return graph
