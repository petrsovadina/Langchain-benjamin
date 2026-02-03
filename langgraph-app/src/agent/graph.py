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

# Runtime import for State dataclass (required for LangGraph type resolution)
from agent.models.drug_models import DrugQuery
from agent.models.research_models import ResearchQuery

# Import MCP infrastructure (Feature 002)
from agent.mcp import SUKLMCPClient, BioMCPClient, MCPConfig

# Import drug_agent_node (Feature 003)
from agent.nodes import drug_agent_node
from agent.nodes.pubmed_agent import pubmed_agent_node

# Import translation and pubmed_agent nodes (Feature 005)
from agent.nodes.translation import translate_cz_to_en_node, translate_en_to_cz_node

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
    print(
        f"[LangSmith] Tracing initialization warning: {e} - continuing without tracing"
    )

# Initialize MCP clients for dev server (Feature 002)
_mcp_config = MCPConfig.from_env()
_sukl_client: SUKLMCPClient | None = None
_biomcp_client: BioMCPClient | None = None

try:
    _sukl_client = SUKLMCPClient(
        base_url=_mcp_config.sukl_url,
        timeout=_mcp_config.sukl_timeout,
        default_retry_config=_mcp_config.to_retry_config()
    )
    print(f"[MCP] SÚKL client initialized: {_mcp_config.sukl_url}")
except Exception as e:
    print(f"[MCP] Failed to initialize SÚKL client: {e} - drug agent will be unavailable")

try:
    _biomcp_client = BioMCPClient(
        base_url=_mcp_config.biomcp_url,
        timeout=_mcp_config.biomcp_timeout,
        max_results=_mcp_config.biomcp_max_results,
        default_retry_config=_mcp_config.to_retry_config()
    )
    print(f"[MCP] BioMCP client initialized: {_mcp_config.biomcp_url}")
except Exception as e:
    print(f"[MCP] Failed to initialize BioMCP client: {e} - PubMed agent will be unavailable")


def get_mcp_clients(runtime: Runtime[Any]) -> tuple[SUKLMCPClient | None, BioMCPClient | None]:
    """Get MCP clients from runtime context with fallback to module-level instances.

    Helper function for nodes to access MCP clients. Checks runtime.context first,
    then falls back to module-level _sukl_client and _biomcp_client initialized
    at module load time from environment variables.

    Args:
        runtime: LangGraph Runtime instance with optional context.

    Returns:
        Tuple of (sukl_client, biomcp_client), either may be None if unavailable.

    Example:
        >>> sukl_client, biomcp_client = get_mcp_clients(runtime)
        >>> if sukl_client:
        ...     result = await sukl_client.call_tool("search_medicine", {...})
    """
    context = runtime.context or {}

    # Try runtime context first (for testing/override)
    sukl = context.get("sukl_mcp_client")
    biomcp = context.get("biomcp_client")

    # Fallback to module-level clients (dev server default)
    if sukl is None:
        sukl = _sukl_client
    if biomcp is None:
        biomcp = _biomcp_client

    return sukl, biomcp


class Context(TypedDict, total=False):
    """Runtime configuration for graph execution.

    Fields:
        model_name: LLM model identifier (e.g., "claude-sonnet-4").
        temperature: Sampling temperature (0.0-1.0).
        langsmith_project: LangSmith project name for tracing.
        user_id: Optional user identifier for session tracking.

        # MCP Clients (Feature 002)
        sukl_mcp_client: SUKLMCPClient - Czech pharmaceutical database client
        biomcp_client: BioMCPClient - International biomedical data client

        # Conversation Tracking (BioAgents-inspired)
        conversation_context: Any  # ConversationContext - persistent state

        # Workflow Mode (BioAgents-inspired)
        mode: Literal["quick", "deep"]  # Quick answer vs deep research

    Example:
        >>> from agent.mcp import SUKLMCPClient, BioMCPClient, MCPConfig
        >>> config = MCPConfig.from_env()
        >>> context: Context = {
        ...     "model_name": "claude-sonnet-4",
        ...     "temperature": 0.0,
        ...     "sukl_mcp_client": SUKLMCPClient(base_url=config.sukl_url),
        ...     "biomcp_client": BioMCPClient(base_url=config.biomcp_url),
        ...     "mode": "quick"
        ... }
    """

    # Core configuration
    model_name: str
    temperature: float
    langsmith_project: str
    user_id: str | None

    # MCP clients (Feature 002 - use Any to avoid Pydantic schema issues)
    # Actual types: SUKLMCPClient, BioMCPClient (from agent.mcp)
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
        drug_query: Optional drug query for SÚKL agent (Feature 003).
        research_query: Optional research query for PubMed agent (Feature 005).
    """

    messages: Annotated[list[AnyMessage], add_messages]
    next: str = "__end__"
    retrieved_docs: list[Document] = field(default_factory=list)
    # Feature 003: SÚKL Drug Agent
    drug_query: DrugQuery | None = None
    # Feature 005: BioMCP PubMed Agent
    research_query: ResearchQuery | None = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults.

        Note: Using field(default_factory=list) for retrieved_docs.
        This method kept for future initialization logic.
        """
        pass


async def placeholder_node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
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
        content = (
            last_message.get("content")
            if isinstance(last_message, dict)
            else last_message.content
        )
        response = f"Echo: {content}"
    else:
        response = "No input"

    return {"messages": [{"role": "assistant", "content": response}], "next": "__end__"}


# Drug-related keywords for routing (Czech + English)
DRUG_KEYWORDS = {
    # Czech
    "lék",
    "léky",
    "léčivo",
    "léčiva",
    "prášky",
    "tablety",
    "pilulky",
    "složení",
    "účinná látka",
    "indikace",
    "kontraindikace",
    "dávkování",
    "úhrada",
    "cena",
    "doplatek",
    "dostupnost",
    "alternativa",
    "súkl",
    "atc",
    "registrační",
    # English fallback
    "drug",
    "medicine",
    "medication",
    "pill",
    "tablet",
    "ingredient",
    "dosage",
    "reimbursement",
    "availability",
}

# Research-related keywords for routing (Czech + English)
RESEARCH_KEYWORDS = {
    # Czech - research terms
    "studie",
    "výzkum",
    "pubmed",
    "článek",
    "články",
    "literatura",
    "pmid",
    "výzkumný",
    "klinická studie",
    "klinický výzkum",
    "randomizovaná studie",
    "meta-analýza",
    "přehled",
    "review",
    "evidence",
    "důkazy",
    "publikace",
    # Czech - medical conditions & treatments (route to research)
    "diabetes",
    "diabetu",
    "diabetem",
    "cukrovka",
    "cukrovkou",
    "léčba",
    "léčení",
    "terapie",
    "onemocnění",
    "nemoc",
    "choroba",
    "syndrom",
    "symptom",
    "příznaky",
    "diagnóza",
    "diagnostika",
    "prevence",
    "prognóza",
    "komplikace",
    "riziko",
    "účinnost",
    "bezpečnost",
    # English fallback
    "study",
    "research",
    "article",
    "literature",
    "paper",
    "clinical trial",
    "meta-analysis",
    "systematic review",
    "evidence",
    "publication",
    "treatment",
    "therapy",
    "disease",
    "diagnosis",
}


def route_query(
    state: State,
) -> Literal["drug_agent", "translate_cz_to_en", "placeholder"]:
    """Route query to appropriate agent based on content.

    Simple keyword-based routing for MVP. Will be replaced by
    Feature 007-supervisor-orchestration with LLM-based intent classification.

    Args:
        state: Current agent state with messages.

    Returns:
        Node name to route to: "drug_agent", "translate_cz_to_en", or "placeholder".
    """
    # Check if explicit drug_query is set
    if state.drug_query is not None:
        return "drug_agent"

    # Check if explicit research_query is set
    if state.research_query is not None:
        return "translate_cz_to_en"

    # Check last user message for keywords
    if state.messages:
        last_message = state.messages[-1]
        raw_content = (
            last_message.get("content", "")
            if isinstance(last_message, dict)
            else getattr(last_message, "content", "")
        )

        # Normalize content to string (handle multimodal list format from LangGraph Studio)
        content_text: str = ""
        if isinstance(raw_content, str):
            content_text = raw_content
        elif isinstance(raw_content, list) and raw_content:
            # Handle multimodal content blocks
            first_block = raw_content[0]
            if isinstance(first_block, str):
                content_text = first_block
            elif isinstance(first_block, dict) and "text" in first_block:
                content_text = str(first_block["text"])

        content_lower = content_text.lower() if content_text else ""

        # Check for research keywords (higher priority - more specific)
        for keyword in RESEARCH_KEYWORDS:
            if keyword in content_lower:
                return "translate_cz_to_en"

        # Check for drug keywords
        for keyword in DRUG_KEYWORDS:
            if keyword in content_lower:
                return "drug_agent"

    # Default to placeholder for non-specific queries
    return "placeholder"


# Build and compile graph with routing
graph = (
    StateGraph(State, context_schema=Context)
    # Add nodes
    .add_node("placeholder", placeholder_node)
    .add_node("drug_agent", drug_agent_node)
    # Feature 005: PubMed research workflow (Sandwich Pattern: CZ→EN→PubMed→EN→CZ)
    .add_node("translate_cz_to_en", translate_cz_to_en_node)
    .add_node("pubmed_agent", pubmed_agent_node)
    .add_node("translate_en_to_cz", translate_en_to_cz_node)
    # Route from start based on query content
    .add_conditional_edges(
        "__start__",
        route_query,
        {
            "drug_agent": "drug_agent",
            "translate_cz_to_en": "translate_cz_to_en",
            "placeholder": "placeholder",
        },
    )
    # Drug agent ends immediately
    .add_edge("drug_agent", "__end__")
    # PubMed research workflow: CZ→EN→PubMed→EN→CZ (Sandwich Pattern)
    .add_edge("translate_cz_to_en", "pubmed_agent")
    .add_edge("pubmed_agent", "translate_en_to_cz")
    .add_edge("translate_en_to_cz", "__end__")
    # Placeholder ends immediately
    .add_edge("placeholder", "__end__")
    .compile(name="Czech MedAI")
)
