# Implementation Plan: LangGraph Foundation

**Branch**: `001-langgraph-foundation` | **Date**: 2026-01-13 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-langgraph-foundation/spec.md`

## Summary

Establish the foundational LangGraph infrastructure for Czech MedAI multi-agent system. This includes defining the `AgentState` schema with message history and document retrieval fields, configuring runtime `Context` for model parameters, setting up pytest testing infrastructure with reusable fixtures, integrating LangSmith tracing for observability, and creating a minimal working graph with one placeholder node to validate the setup.

**Technical Approach**: Use LangGraph's TypedDict-based state management with annotated fields for message aggregation. Implement async node functions following the `Runtime[Context]` pattern. Configure pytest with fixtures for mocked state/runtime. Enable LangSmith via environment variables with graceful degradation.

## Technical Context

**Language/Version**: Python ≥3.10 (per constitution)  
**Primary Framework**: LangGraph ≥1.0.0 (per constitution)  
**Additional Dependencies**: 
- `langgraph>=1.0.0` (core framework)
- `langchain-core>=0.3.0` (for Document, AnyMessage types)
- `python-dotenv>=1.0.1` (for environment variable management)
- `langsmith>=0.2.0` (for tracing)
- `pytest>=8.3.5` (per constitution)
- `pytest-asyncio>=0.24.0` (for async test support)

**Storage**: In-memory state only (no persistence in this feature)  
**Testing**: pytest with async support (per constitution)  
**Target Platform**: LangGraph Server via `langgraph dev`  
**Project Type**: LangGraph Agent (single graph in `src/agent/graph.py`)  
**Performance Goals**: 
- Graph compilation: <500ms
- Placeholder node execution: <50ms
- Test suite execution: <3s

**Constraints**: 
- Async-first (per constitution)
- Minimal external deps (only LangGraph ecosystem)
- Type-safe (mypy --strict compliance)

**Scale/Scope**: 
- 1 placeholder node in this feature
- State schema supports future 4-6 specialized agents
- Extensible Context for multi-model support

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Graph-Centric Architecture
- ✅ Feature designed as LangGraph nodes/edges in `src/agent/graph.py`
- ✅ All nodes follow async signature: `async def placeholder_node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- ✅ State transitions explicit via `.add_edge("__start__", "placeholder_node")`
- ✅ Graph structure visualizable in LangGraph Studio (single node graph)

### Principle II: Type Safety & Schema Validation
- ✅ `State` dataclass defined with typed fields: `messages`, `next`, `retrieved_docs`
- ✅ `Context` TypedDict defined with runtime params: `model_name`, `temperature`, `langsmith_project`
- ✅ All node inputs/outputs typed correctly (Dict[str, Any] return type)
- ⚠️ Pydantic models N/A (no external data in this feature)

### Principle III: Test-First Development
- ✅ Unit tests planned for placeholder node in `tests/unit_tests/test_foundation.py`
- ✅ Integration tests planned for graph execution in `tests/integration_tests/test_graph_foundation.py`
- ✅ Test-first workflow confirmed: Write test → Fail → Implement → Pass

### Principle IV: Observability & Debugging
- ✅ LangSmith tracing enabled (LANGSMITH_API_KEY in .env)
- ✅ Logging added at placeholder node entry/exit
- ✅ State transitions logged using `print()` (structured logging post-MVP)
- ✅ Testing plan includes LangGraph Studio verification

### Principle V: Modular & Extensible Design
- ✅ Placeholder node is single-responsibility (echo messages)
- ✅ Reusable logic: State/Context definitions used by all future agents
- ✅ Configuration parameters use Context (`model_name`, `temperature`)
- ⚠️ Subgraphs N/A (single node in this feature)

**✅ Constitution Check: PASSED** (all critical principles satisfied)

## Project Structure

### Documentation (this feature)

```text
specs/001-langgraph-foundation/
├── spec.md              # Feature specification (DONE)
├── plan.md              # This file (DONE)
└── tasks.md             # Task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
langgraph-app/
├── src/
│   └── agent/
│       ├── __init__.py          # Package initialization
│       └── graph.py             # Main graph with State, Context, placeholder node
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures (sample_state, mock_runtime, test_graph)
│   ├── unit_tests/
│   │   ├── __init__.py
│   │   └── test_foundation.py  # Unit tests for placeholder node
│   └── integration_tests/
│       ├── __init__.py
│       └── test_graph_foundation.py  # Integration test for graph invocation
├── .env.example                 # Template for environment variables
├── pyproject.toml               # Dependencies already configured
├── langgraph.json               # LangGraph server config
└── README.md                    # Project README (update with foundation setup)
```

**Files Modified**:
- `langgraph-app/src/agent/graph.py` - Replace template with AgentState, Context, placeholder_node
- `langgraph-app/tests/conftest.py` - Add pytest fixtures
- New files: `test_foundation.py`, `test_graph_foundation.py`, `.env.example`

## Phase 0: Research & Dependencies

### Research Topics

1. **LangGraph State Management Best Practices**
   - Review: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
   - Focus: Annotated fields with reducers (add_messages pattern)
   - Key learning: How to properly type `messages` field for multi-turn conversations

2. **Runtime Context Patterns**
   - Review: https://langchain-ai.github.io/langgraph/agents/context/
   - Focus: Static vs dynamic context, accessing via `runtime.context`
   - Key learning: Best practices for configuration management in multi-agent systems

3. **LangSmith Tracing Integration**
   - Review: https://docs.smith.langchain.com/tracing/faq/logging_and_viewing
   - Focus: Environment variable configuration, graceful degradation
   - Key learning: How to enable tracing without breaking local development

4. **Pytest Async Testing with LangGraph**
   - Review: https://pytest-asyncio.readthedocs.io/
   - Focus: Fixtures for async functions, mocking Runtime objects
   - Key learning: Strategies for testing async graph invocations

### Dependency Analysis

**Required (already in pyproject.toml)**:
- ✅ `langgraph>=1.0.0`
- ✅ `python-dotenv>=1.0.1`
- ✅ `pytest>=8.3.5` (dev)

**To Add**:
- `langchain-core>=0.3.0` - For Document, AnyMessage types
- `pytest-asyncio>=0.24.0` - For async test support
- `langsmith>=0.2.0` - For tracing (optional runtime dependency)

**Installation**:
```bash
cd langgraph-app
pip install langchain-core pytest-asyncio langsmith
```

## Phase 1: Data Model

### State Schema Definition

```python
from dataclasses import dataclass
from typing import Annotated, Any
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langchain_core.documents import Document
from langgraph.graph.message import add_messages

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
    retrieved_docs: list[Document] = None
    
    def __post_init__(self):
        """Initialize mutable defaults."""
        if self.retrieved_docs is None:
            self.retrieved_docs = []
```

### Context Schema Definition

```python
from typing import Literal

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
```

**Design Decisions**:
- `total=False` allows optional Context fields (graceful defaults)
- `retrieved_docs` as list (not dict) for simpler citation ordering
- `next` field enables supervisor routing pattern (future features)
- MCP client fields use `Any` type in foundation (strongly typed in Feature 002)
- `mode` field enables dual workflow pattern (90% quick, 10% deep research)
- `conversation_context` placeholder for persistent state (implemented in Feature 013)

### ConversationContext Pattern (BioAgents-Inspired)

**Purpose**: Separate ephemeral message-level state from persistent conversation-level state. Prevents state bloat while maintaining research context across sessions.

**Pattern Overview** (implementation in Feature 013):

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class ConversationContext:
    """Persistent state across conversation sessions.

    Stored in database, not in LangGraph State (which is ephemeral).
    Enables multi-turn research with knowledge accumulation.
    """
    # Identification
    conversation_id: str
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Medical Context (Czech MedAI specific)
    patient_context: Optional[dict] = None  # Patient history if applicable
    previous_queries: list[str] = field(default_factory=list)

    # Knowledge Accumulation
    retrieved_medicines: list[dict] = field(default_factory=list)  # SÚKL results
    cited_studies: list[dict] = field(default_factory=list)        # PubMed citations
    clinical_insights: list[str] = field(default_factory=list)     # Key findings

    # Research Tracking (for deep mode)
    active_hypotheses: list[dict] = field(default_factory=list)
    research_objectives: list[str] = field(default_factory=list)
    task_history: list[dict] = field(default_factory=list)
```

**State Management Layers**:

1. **Message State** (LangGraph `State`):
   - Ephemeral, auto-cleared after response
   - Fields: `messages`, `next`, `retrieved_docs`
   - Lifespan: Single graph execution

2. **Conversation State** (`ConversationContext`):
   - Persistent, stored in database
   - Fields: Medical context, accumulated knowledge, hypotheses
   - Lifespan: Entire conversation (days/weeks)

3. **Runtime Context** (LangGraph `Context`):
   - Configuration parameters
   - Fields: `model_name`, `temperature`, MCP clients
   - Lifespan: Single invocation

**Integration Point**: `Context.conversation_context` field references the persistent object loaded from database at graph invocation start.

**Implementation Note**: Foundation feature (001) only defines the placeholder field. Actual implementation happens in Feature 013 (Workflow Modes) with Supabase persistence.

## Phase 2: Implementation Details

### File 1: `langgraph-app/src/agent/graph.py`

**Placeholder Node Implementation**:

```python
from typing import Any, Dict
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

async def placeholder_node(
    state: State, 
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Echo user messages with configuration info.
    
    Args:
        state: Current agent state with message history.
        runtime: Runtime context with configuration.
    
    Returns:
        Updated state with AI response message.
    """
    model = runtime.context.get("model_name", "default")
    
    # Log for debugging
    print(f"[placeholder_node] Executing with model={model}")
    
    # Echo last user message
    last_message = state.messages[-1] if state.messages else None
    response = f"Echo: {last_message.content}" if last_message else "No input"
    
    return {
        "messages": [{"role": "assistant", "content": response}],
        "next": "__end__"
    }
```

**Graph Compilation**:

```python
# Build and compile graph
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("placeholder", placeholder_node)
    .add_edge("__start__", "placeholder")
    .add_edge("placeholder", "__end__")
    .compile(name="Czech MedAI Foundation")
)
```

### MCP Client Initialization Pattern

**Purpose**: Prepare runtime Context with MCP client instances for SÚKL-mcp and BioMCP servers. Enables agents to query external data sources through Model Context Protocol.

**Implementation Pattern** (from Feature 002):

```python
from typing import Any
import os

# Placeholder wrappers (implemented fully in Feature 002)
class SUKLMCPClient:
    """Wrapper for SÚKL-mcp server (Czech pharmaceutical DB)."""

    def __init__(self, url: str, transport: str = "http"):
        self.url = url
        self.transport = transport

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call MCP tool (placeholder - real implementation in Feature 002)."""
        raise NotImplementedError("SÚKL-mcp integration pending Feature 002")

class BioMCPClient:
    """Wrapper for BioMCP server (biomedical databases)."""

    def __init__(self, transport: str = "stdio", command: str = "biomcp run"):
        self.transport = transport
        self.command = command

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call MCP tool (placeholder - real implementation in Feature 002)."""
        raise NotImplementedError("BioMCP integration pending Feature 002")

# Graph invocation with MCP clients
async def invoke_with_mcp():
    """Example: Invoke graph with MCP clients in context."""

    # Initialize clients from environment
    sukl_client = SUKLMCPClient(
        url=os.getenv("SUKL_MCP_URL", "https://SUKL-mcp.fastmcp.app/mcp"),
        transport=os.getenv("SUKL_MCP_TRANSPORT", "http")
    )

    biomcp_client = BioMCPClient(
        transport=os.getenv("BIOMCP_TRANSPORT", "stdio"),
        command=os.getenv("BIOMCP_COMMAND", "biomcp run")
    )

    # Build context with clients
    context = {
        "model_name": "claude-sonnet-4",
        "temperature": 0.0,
        "sukl_mcp_client": sukl_client,
        "biomcp_client": biomcp_client,
        "mode": "quick"  # Default to quick answer mode
    }

    # Invoke graph
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "Co je Paralen?"}]},
        context=context
    )

    return result
```

**Usage in Agent Nodes** (from Feature 003+):

```python
async def drug_agent_node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Query SÚKL database for drug information."""

    # Access MCP client from context
    sukl_client = runtime.context.get("sukl_mcp_client")

    if sukl_client is None:
        # Graceful degradation if MCP not available
        return {
            "messages": [{"role": "assistant", "content": "SÚKL database nedostupná"}],
            "next": "__end__"
        }

    # Call MCP tool
    query = state.messages[-1].content
    result = await sukl_client.call_tool(
        "search_medicine",
        query=query,
        fuzzy=True,
        max_results=10
    )

    # Process results
    medicines = result.get("medicines", [])
    docs = [Document(page_content=m["name"], metadata=m) for m in medicines]

    return {
        "retrieved_docs": docs,
        "next": "synthesizer"
    }
```

**Implementation Note**: Foundation feature (001) only defines the Context placeholder fields. Actual MCP client implementations happen in Feature 002 (MCP Infrastructure). Features 003-006 use the clients for specialized agents.

### File 2: `langgraph-app/tests/conftest.py`

```python
import pytest
from src.agent.graph import State, Context, graph

@pytest.fixture
def sample_state():
    """Provide a valid State instance for testing."""
    return State(
        messages=[{"role": "user", "content": "test message"}],
        next="placeholder",
        retrieved_docs=[]
    )

@pytest.fixture
def mock_runtime():
    """Provide a mock Runtime with default context."""
    class MockRuntime:
        def __init__(self):
            self.context = {
                "model_name": "test-model",
                "temperature": 0.0,
                "langsmith_project": "test-project"
            }
    return MockRuntime()

@pytest.fixture
def test_graph():
    """Provide the compiled graph for integration tests."""
    return graph
```

### File 3: `.env.example`

```bash
# LangSmith Tracing (optional)
LANGSMITH_API_KEY=lsv2_pt_your_key_here
LANGSMITH_PROJECT=czech-medai-dev
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Development Settings
LOG_LEVEL=INFO
```

## Testing Strategy

### Unit Tests (`test_foundation.py`)

```python
import pytest
from src.agent.graph import placeholder_node, State

@pytest.mark.asyncio
async def test_placeholder_node_echoes_message(mock_runtime):
    """Test placeholder node echoes user message."""
    state = State(
        messages=[{"role": "user", "content": "Hello"}],
        next="placeholder"
    )
    
    result = await placeholder_node(state, mock_runtime)
    
    assert "Echo: Hello" in result["messages"][0]["content"]
    assert result["next"] == "__end__"

@pytest.mark.asyncio
async def test_placeholder_node_handles_empty_state(mock_runtime):
    """Test placeholder node with no messages."""
    state = State(messages=[], next="placeholder")
    
    result = await placeholder_node(state, mock_runtime)
    
    assert result["messages"][0]["content"] == "No input"
```

### Integration Tests (`test_graph_foundation.py`)

```python
import pytest

@pytest.mark.asyncio
async def test_graph_invocation_returns_state(test_graph):
    """Test graph can be invoked and returns valid state."""
    input_state = {
        "messages": [{"role": "user", "content": "test"}]
    }
    context = {
        "model_name": "test-model",
        "temperature": 0.0
    }
    
    result = await test_graph.ainvoke(input_state, context=context)
    
    assert "messages" in result
    assert len(result["messages"]) == 2  # User + AI message

@pytest.mark.asyncio  
async def test_graph_renders_in_studio(test_graph):
    """Test graph structure is valid for visualization."""
    graph_dict = test_graph.get_graph().to_json()
    
    assert "nodes" in graph_dict
    assert "placeholder" in [n["id"] for n in graph_dict["nodes"]]
```

## Acceptance Criteria Checklist

- [ ] `AgentState` and `Context` definitions pass `mypy --strict`
- [ ] Placeholder node follows async signature from constitution
- [ ] Graph compiles without errors and names is "Czech MedAI Foundation"
- [ ] Running `pytest langgraph-app/tests/` passes all tests with ≥80% coverage
- [ ] Graph renders correctly in LangGraph Studio (manual verification)
- [ ] LangSmith traces appear when `LANGSMITH_API_KEY` is set (manual verification)
- [ ] Running `ruff check langgraph-app/src/` produces zero errors
- [ ] All docstrings follow Google style and pass D401 rule

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LangGraph API changes between versions | HIGH | LOW | Pin exact version in pyproject.toml: `langgraph==1.0.x` |
| Pytest async fixtures not working | MEDIUM | LOW | Use `pytest-asyncio` with explicit markers |
| LangSmith tracing breaks local dev | MEDIUM | MEDIUM | Implement try/except around tracing initialization |
| Type hints too strict for prototyping | LOW | MEDIUM | Use `typing.Any` where needed, refine in later features |

## Next Steps After This Feature

1. **Feature 002-mcp-infrastructure**: Parallel work on MCP protocol setup
2. **Feature 003-sukl-drug-agent**: First specialized agent using this foundation
3. **Documentation**: Update main README with foundation setup instructions

## References

- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangSmith Setup**: https://docs.smith.langchain.com/
- **Constitution**: Principles I-V (all applied in this feature)
- **PRD**: MVP Spec §3.1, Architecture §2.1
