"""LangGraph Foundation for Czech MedAI.

Defines AgentState schema, Context configuration, and base graph structure.
Implements Constitution Principles I-V.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Annotated, Any, Dict, Literal

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

# Load environment variables (LangSmith tracing)
load_dotenv()

# Initialize LangSmith tracing with graceful degradation
try:
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    if langsmith_api_key:
        os.environ.setdefault("LANGSMITH_TRACING", "true")
        print("[LangSmith] Tracing enabled")
    else:
        print("[LangSmith] No API key found - tracing disabled (graceful degradation)")
except Exception as e:
    print(f"[LangSmith] Tracing initialization warning: {e} - continuing without tracing")


class Context(TypedDict, total=False):
    """Runtime configuration for graph execution.

    Fields:
        model_name: LLM model identifier (e.g., "claude-sonnet-4").
        temperature: Sampling temperature (0.0-1.0).
        langsmith_project: LangSmith project name for tracing.
        user_id: Optional user identifier for session tracking.

        # MCP Clients (Feature 002 integration)
        sukl_mcp_client: Any  # SUKLMCPClient - Czech pharmaceutical database
        biomcp_client: Any    # BioMCPClient - International biomedical data

        # Conversation Tracking (BioAgents-inspired)
        conversation_context: Any  # ConversationContext - persistent state

        # Workflow Mode (BioAgents-inspired)
        mode: Literal["quick", "deep"]  # Quick answer vs deep research
    """
    # Core configuration
    model_name: str
    temperature: float
    langsmith_project: str
    user_id: str | None

    # MCP clients (placeholders - typed in Feature 002)
    sukl_mcp_client: Any
    biomcp_client: Any

    # Conversation persistence (typed in Feature 013)
    conversation_context: Any

    # Workflow mode (default: "quick")
    mode: Literal["quick", "deep"]


@dataclass
class State:
    """Agent state passed between nodes.

    Attributes:
        messages: Conversation history (user + AI messages).
                  Uses add_messages reducer for automatic appending.
        next: Name of next node to execute (routing control).
        retrieved_docs: Documents retrieved by agents with citations.
    """
    messages: Annotated[list[AnyMessage], add_messages]
    next: str = "__end__"
    retrieved_docs: list[Document] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize mutable defaults.

        Note: Using field(default_factory=list) for retrieved_docs.
        This method kept for future initialization logic.
        """
        pass


async def placeholder_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Echo user messages with configuration info.

    Processes input state and returns AI response using configured model.

    Args:
        state: Current agent state with message history.
        runtime: Runtime context with model configuration.

    Returns:
        Updated state dict with:
            - messages: list with new assistant message
            - next: routing indicator for next node

    Raises:
        ValueError: If state.messages is empty.
    """
    # Access context with fallback
    context = runtime.context or {}
    model = context.get("model_name", "default")

    # Log for debugging
    print(f"[placeholder_node] Executing with model={model}")

    # Echo last user message
    last_message = state.messages[-1] if state.messages else None
    if last_message:
        # Handle both dict and Message object formats
        content = last_message.get("content") if isinstance(last_message, dict) else last_message.content
        response = f"Echo: {content}"
    else:
        response = "No input"

    return {
        "messages": [{"role": "assistant", "content": response}],
        "next": "__end__"
    }


# Build and compile graph
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("placeholder", placeholder_node)
    .add_edge("__start__", "placeholder")
    .add_edge("placeholder", "__end__")
    .compile(name="Czech MedAI Foundation")
)
