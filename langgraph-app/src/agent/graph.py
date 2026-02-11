"""LangGraph Foundation for Czech MedAI.

Defines AgentState schema, Context configuration, and base graph structure.
Implements Constitution Principles I-V.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, Sequence

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.runtime import Runtime
from langgraph.types import Command, Send
from typing_extensions import TypedDict

# Import MCP infrastructure (Feature 002)
from agent.mcp import BioMCPClient, MCPConfig, SUKLMCPClient

# Runtime import for State dataclass (required for LangGraph type resolution)
from agent.models.drug_models import DrugQuery
from agent.models.guideline_models import GuidelineQuery
from agent.models.research_models import ResearchQuery

# Import drug_agent_node (Feature 003)
from agent.nodes import drug_agent_node
from agent.nodes.guidelines_agent import guidelines_agent_node
from agent.nodes.pubmed_agent import pubmed_agent_node

# Import supervisor node (Feature 007)
from agent.nodes.supervisor import supervisor_node

# Import synthesizer node (Feature 009)
from agent.nodes.synthesizer import synthesizer_node

# Import translation and pubmed_agent nodes (Feature 005)
from agent.nodes.translation import translate_cz_to_en_node, translate_en_to_cz_node
from agent.utils.message_utils import extract_message_content

# Load environment variables (LangSmith tracing)
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize LangSmith tracing with graceful degradation
try:
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    if langsmith_api_key:
        os.environ.setdefault("LANGSMITH_TRACING", "true")
        logger.info("LangSmith tracing enabled")
    else:
        logger.info("LangSmith: No API key found - tracing disabled (graceful degradation)")
except (ImportError, OSError, ValueError) as e:
    logger.warning("LangSmith tracing initialization warning: %s - continuing without tracing", e)

# Initialize MCP clients for dev server (Feature 002)
_mcp_config = MCPConfig.from_env()
_sukl_client: SUKLMCPClient | None = None
_biomcp_client: BioMCPClient | None = None

try:
    _sukl_client = SUKLMCPClient(
        base_url=_mcp_config.sukl_url,
        timeout=_mcp_config.sukl_timeout,
        default_retry_config=_mcp_config.to_retry_config(),
    )
    logger.info("SÚKL MCP client initialized: %s", _mcp_config.sukl_url)
except (OSError, ConnectionError, ValueError) as e:
    logger.warning("Failed to initialize SÚKL client: %s - drug agent will be unavailable", e)

try:
    _biomcp_client = BioMCPClient(
        base_url=_mcp_config.biomcp_url,
        timeout=_mcp_config.biomcp_timeout,
        max_results=_mcp_config.biomcp_max_results,
        default_retry_config=_mcp_config.to_retry_config(),
    )
    logger.info("BioMCP client initialized: %s", _mcp_config.biomcp_url)
except (OSError, ConnectionError, ValueError) as e:
    logger.warning("Failed to initialize BioMCP client: %s - PubMed agent will be unavailable", e)


def get_mcp_clients(
    runtime: Runtime[Any],
) -> tuple[SUKLMCPClient | None, BioMCPClient | None]:
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


def _keep_last(existing: str, new: str) -> str:
    """Reducer for next field: keep last value (supports parallel agent updates)."""
    return new


def add_documents(
    existing: Sequence[Document],
    new: Sequence[Document],
) -> list[Document]:
    """Reducer for appending documents (similar to add_messages).

    Appends new documents to existing list instead of replacing.
    Used for parallel agent execution where multiple agents contribute
    documents to state.retrieved_docs.

    Args:
        existing: Current documents in state.
        new: New documents to append.

    Returns:
        Combined list of documents.
    """
    return list(existing) + list(new)


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

        # API Keys (Feature 006)
        openai_api_key: OpenAI API key for embeddings (guidelines semantic search)

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

    # API Keys (Feature 006)
    openai_api_key: str

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
        guideline_query: Optional guideline query for Guidelines agent (Feature 006).
    """

    messages: Annotated[list[AnyMessage], add_messages]
    next: Annotated[str, _keep_last] = "__end__"
    retrieved_docs: Annotated[list[Document], add_documents] = field(
        default_factory=list
    )
    # Feature 003: SÚKL Drug Agent
    drug_query: DrugQuery | None = None
    # Feature 005: BioMCP PubMed Agent
    research_query: ResearchQuery | None = None
    # Feature 006: Guidelines Agent
    guideline_query: GuidelineQuery | None = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults.

        Note: Using field(default_factory=list) for retrieved_docs.
        This method kept for future initialization logic.
        """
        pass


async def placeholder_node(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
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

    logger.debug("placeholder_node executing with model=%s", model)

    # Echo last user message
    last_message = state.messages[-1] if state.messages else None
    if last_message:
        content = extract_message_content(last_message)
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
    # Czech - research-SPECIFIC terms (must clearly indicate research intent)
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
    "review",
    "evidence",
    "důkazy",
    "publikace",
    # English fallback - research specific
    "study",
    "research",
    "article",
    "literature",
    "paper",
    "clinical trial",
    "meta-analysis",
    "systematic review",
    "publication",
}

# Generic medical terms - these alone DON'T indicate research intent.
# They're used by the LLM classifier (supervisor) for context, NOT keyword routing.
# Moved OUT of RESEARCH_KEYWORDS to fix routing overlap:
# "léčba", "léčení", "terapie", "onemocnění", "nemoc", "choroba",
# "syndrom", "symptom", "příznaky", "diagnóza", "diagnostika",
# "prevence", "prognóza", "komplikace", "riziko", "účinnost",
# "bezpečnost", "diabetes", "diabetu", "cukrovka", etc.

# Guidelines-related keywords for routing (Czech + English)
GUIDELINES_KEYWORDS = {
    # Czech
    "guidelines",
    "doporučené postupy",
    "doporučení",
    "standardy",
    "standard",
    "protokol",
    "algoritmus",
    "cls jep",
    "cls-jep",
    "esc",
    "ers",
    "léčebný postup",
    "diagnostický postup",
    "klinické doporučení",
    # English fallback
    "guideline",
    "recommendation",
    "protocol",
    "algorithm",
    "clinical practice",
}


def route_query(
    state: State,
) -> Literal["drug_agent", "translate_cz_to_en", "guidelines_agent", "placeholder"]:
    """Route query to appropriate agent based on content.

    Simple keyword-based routing as fallback for supervisor LLM classification.

    Routing priority:
    1. Explicit queries (drug_query, research_query, guideline_query)
    2. Drug keywords (highest - most common use case)
    3. Research keywords (research-specific terms only)
    4. Guidelines keywords
    5. Placeholder (fallback)

    Args:
        state: Current agent state with messages.

    Returns:
        Node name to route to: "drug_agent", "translate_cz_to_en", "guidelines_agent", or "placeholder".
    """
    # Check if explicit drug_query is set
    if state.drug_query is not None:
        return "drug_agent"

    # Check if explicit research_query is set
    if state.research_query is not None:
        return "translate_cz_to_en"

    # Check if explicit guideline_query is set
    if state.guideline_query is not None:
        return "guidelines_agent"

    # Check last user message for keywords
    if state.messages:
        last_message = state.messages[-1]
        content_text = extract_message_content(last_message)
        content_lower = content_text.lower() if content_text else ""

        # Check for drug keywords FIRST (most common use case)
        for keyword in DRUG_KEYWORDS:
            if keyword in content_lower:
                return "drug_agent"

        # Check for research keywords (now trimmed to research-specific terms)
        for keyword in RESEARCH_KEYWORDS:
            if keyword in content_lower:
                return "translate_cz_to_en"

        # Check for guidelines keywords
        for keyword in GUIDELINES_KEYWORDS:
            if keyword in content_lower:
                return "guidelines_agent"

    # Default to placeholder for non-specific queries
    return "placeholder"


async def _supervisor_with_command(
    state: State, runtime: Runtime[Context]
) -> Command[str]:
    """Convert supervisor_node Send returns to Command for graph compatibility.

    supervisor_node returns Send | list[Send] for unit-test convenience,
    but compiled LangGraph nodes must return dict or Command.
    """
    result = await supervisor_node(state, runtime)
    if isinstance(result, list):
        return Command(goto=result)
    elif isinstance(result, Send):
        return Command(goto=[result])
    return result


# Build and compile graph with Send API routing
graph = (
    StateGraph(State, context_schema=Context)
    # Add nodes
    # Feature 007: Supervisor orchestrator (LLM-based intent classification + Send API)
    .add_node("supervisor", _supervisor_with_command)
    .add_node("placeholder", placeholder_node)
    .add_node("drug_agent", drug_agent_node)
    # Feature 005: PubMed research workflow (Sandwich Pattern: CZ→EN→PubMed→EN→CZ)
    .add_node("translate_cz_to_en", translate_cz_to_en_node)
    .add_node("pubmed_agent", pubmed_agent_node)
    .add_node("translate_en_to_cz", translate_en_to_cz_node)
    # Feature 006: Guidelines Agent
    .add_node("guidelines_agent", guidelines_agent_node)
    # Feature 009: Synthesizer (combines multi-agent responses)
    .add_node("synthesizer", synthesizer_node)
    # Entry point
    .add_edge("__start__", "supervisor")
    # Supervisor uses Send API for dynamic routing (no conditional edges needed)
    # Agent edges route to synthesizer (Feature 009)
    .add_edge("drug_agent", "synthesizer")
    # PubMed research workflow: CZ→EN→PubMed→EN→CZ (Sandwich Pattern)
    .add_edge("translate_cz_to_en", "pubmed_agent")
    .add_edge("pubmed_agent", "translate_en_to_cz")
    .add_edge("translate_en_to_cz", "synthesizer")
    # Guidelines agent routes to synthesizer
    .add_edge("guidelines_agent", "synthesizer")
    # Placeholder routes to synthesizer
    .add_edge("placeholder", "synthesizer")
    # Synthesizer ends the graph
    .add_edge("synthesizer", "__end__")
    .compile(name="Czech MedAI")
)
