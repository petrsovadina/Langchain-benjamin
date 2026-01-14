# Feature Specification: LangGraph Foundation

**Feature Branch**: `001-langgraph-foundation`  
**Created**: 2026-01-13  
**Status**: Draft  
**Input**: Setup LangGraph foundation with State schema, Context configuration, pytest fixtures, LangSmith tracing, and base graph structure

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define Agent State Schema (Priority: P1)

As a developer building Czech MedAI agents, I need a strongly-typed `AgentState` schema that all nodes can use to pass data, so that I can ensure type safety and prevent runtime errors during graph execution.

**Why this priority**: This is the foundational data structure that ALL subsequent agents depend on. Without a well-defined state schema, we cannot implement any nodes.

**Independent Test**: Can be fully tested by instantiating `AgentState` with valid/invalid data and verifying TypedDict validation. Delivers a contract that all future nodes must follow.

**Acceptance Scenarios**:

1. **Given** a new LangGraph project, **When** I import `AgentState` from `src/agent/graph.py`, **Then** I can access fields: `messages`, `next`, `retrieved_docs` with correct types
2. **Given** a node function signature, **When** I type-hint the state parameter as `State`, **Then** mypy validation passes without errors
3. **Given** an `AgentState` instance, **When** I add a message using `add_messages` annotator, **Then** the message is appended to the messages list correctly

---

### User Story 2 - Configure Runtime Context (Priority: P1)

As a developer, I need a `Context` TypedDict for runtime configuration parameters (API keys, model names, user preferences), so that I can make the graph behavior configurable without hardcoding values.

**Why this priority**: Configuration must be separated from code (constitution Principle V). This enables testing with different configurations and user-specific settings.

**Independent Test**: Can be tested by invoking graph with different Context values and verifying nodes receive correct runtime parameters.

**Acceptance Scenarios**:

1. **Given** a `Context` definition, **When** I define fields like `model_name`, `temperature`, `user_id`, **Then** the Context TypedDict validates these fields
2. **Given** a graph invocation, **When** I pass `context={"model_name": "claude-sonnet-4"}`, **Then** nodes can access `runtime.context["model_name"]`
3. **Given** missing required context fields, **When** graph is invoked, **Then** a clear validation error is raised

---

### User Story 3 - Setup Pytest Testing Infrastructure (Priority: P1)

As a developer, I need pytest fixtures for creating test graphs and mocked state, so that I can write unit tests for individual nodes without spinning up the entire system.

**Why this priority**: Test-first development (Principle III) is non-negotiable. Without test infrastructure, we cannot validate any implementation.

**Independent Test**: Can be tested by writing a sample test that uses fixtures to create a minimal graph and assert state transitions.

**Acceptance Scenarios**:

1. **Given** `conftest.py` with fixtures, **When** I write a test function using `@pytest.fixture` for `sample_state`, **Then** the fixture provides a valid `AgentState` instance
2. **Given** a test for a node function, **When** I use the `mock_runtime` fixture, **Then** I can test node logic without external dependencies
3. **Given** multiple tests, **When** I run `pytest langgraph-app/tests/`, **Then** all foundation tests pass with coverage >80%

---

### User Story 4 - Integrate LangSmith Tracing (Priority: P2)

As a developer, I need LangSmith tracing configured in the graph, so that I can debug graph executions and monitor production performance.

**Why this priority**: Observability (Principle IV) is critical for debugging multi-agent systems, but can be added after basic graph structure works.

**Independent Test**: Can be tested by invoking the graph with `LANGSMITH_API_KEY` set and verifying traces appear in LangSmith dashboard.

**Acceptance Scenarios**:

1. **Given** `.env` file with `LANGSMITH_API_KEY=lsv2_...`, **When** I run the graph, **Then** execution traces appear in LangSmith project
2. **Given** a graph execution, **When** I view the trace in LangSmith, **Then** I can see individual node executions, latencies, and inputs/outputs
3. **Given** LangSmith is unavailable, **When** graph executes, **Then** it continues without crashing (graceful degradation)

---

### User Story 5 - Create Base Graph Structure (Priority: P1)

As a developer, I need a minimal working LangGraph with a single placeholder node, so that I can verify the graph compiles and executes before adding complex agents.

**Why this priority**: This validates the entire foundation setup works end-to-end. It's the "hello world" of our multi-agent system.

**Independent Test**: Can be tested by invoking the graph with a simple message and asserting it returns a response.

**Acceptance Scenarios**:

1. **Given** `src/agent/graph.py` with a compiled graph, **When** I import and invoke it with `graph.invoke({"messages": [...]})`, **Then** it returns a valid state object
2. **Given** the base graph, **When** I visualize it using `graph.get_graph().draw_mermaid()`, **Then** I can see nodes and edges in ASCII/Mermaid format
3. **Given** LangGraph Studio, **When** I open the project, **Then** the graph renders correctly in the visual debugger

---

### Edge Cases

- What happens when `AgentState` is instantiated with invalid field types (e.g., `messages` as string instead of list)?
- How does the graph handle missing `Context` fields that nodes expect to be present?
- What happens if LangSmith tracing fails to initialize (network error, invalid API key)?
- How does pytest handle async node functions during testing?
- What happens when a node modifies state fields that aren't declared in `AgentState`?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST define `AgentState` as a TypedDict with fields: `messages: Annotated[list[AnyMessage], add_messages]`, `next: str`, `retrieved_docs: list[Document]`
- **FR-002**: System MUST define `Context` as a TypedDict with at least: `model_name: str`, `temperature: float`, `langsmith_project: str`
- **FR-003**: System MUST provide pytest fixtures in `langgraph-app/tests/conftest.py` including: `sample_state`, `mock_runtime`, `test_graph`
- **FR-004**: System MUST configure LangSmith tracing using environment variables (`LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`)
- **FR-005**: System MUST create a minimal graph with one placeholder node that echoes input messages
- **FR-006**: Graph MUST be compiled using `StateGraph(State, context_schema=Context).compile(name="Czech MedAI")`
- **FR-007**: All node functions MUST follow async signature: `async def node_name(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- **FR-008**: System MUST pass `ruff` linting with no errors
- **FR-009**: All functions MUST have type hints enforced by `mypy --strict`
- **FR-010**: All node functions MUST have Google-style docstrings

### Key Entities

- **AgentState**: The shared state object passed between nodes. Contains conversation history (`messages`), routing information (`next`), and retrieved documents (`retrieved_docs`).
- **Context**: Runtime configuration for the graph. Contains model settings, API keys (via env vars), and user-specific preferences.
- **Runtime**: LangGraph-provided object available in nodes, giving access to `Context` via `runtime.context`.
- **Document**: LangChain document type used in `retrieved_docs` for storing citations with metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developer can instantiate `AgentState` and `Context` without type errors (verified by `mypy --strict`)
- **SC-002**: Running `pytest langgraph-app/tests/` produces ≥80% code coverage for foundation modules
- **SC-003**: Graph compiles successfully and can be invoked with `graph.invoke()` returning valid state in <100ms
- **SC-004**: LangSmith traces appear for graph executions when `LANGSMITH_API_KEY` is set (verifiable in dashboard)
- **SC-005**: Graph renders correctly in LangGraph Studio with all nodes and edges visible
- **SC-006**: Running `ruff check langgraph-app/src/` produces zero linting errors
- **SC-007**: All docstrings pass `ruff` D401 rule (imperative mood for first line)
- **SC-008**: Developer can write a new test using provided fixtures in <5 minutes (documentation test)

## Non-Functional Requirements

### Performance

- **NFR-001**: Graph initialization (compile) MUST complete in <500ms
- **NFR-002**: Placeholder node execution MUST complete in <50ms
- **NFR-003**: Pytest test suite for foundation MUST run in <3 seconds

### Observability

- **NFR-004**: All node executions MUST be traceable in LangSmith with input/output logs
- **NFR-005**: State transitions MUST be logged at INFO level for debugging

### Maintainability

- **NFR-006**: Code MUST follow LangGraph patterns from official documentation
- **NFR-007**: Type hints MUST cover 100% of function signatures
- **NFR-008**: Test fixtures MUST be reusable for all future agent implementations

## References

- **Constitution**: Principles I (Graph-Centric), II (Type Safety), III (Test-First), IV (Observability)
- **PRD**: MVP Spec §3.1 (High-Level Architecture), Tech Doc §2.1 (State Schema)
- **LangGraph Docs**: [State Management](https://langchain-ai.github.io/langgraph/concepts/low_level/#state), [Context](https://langchain-ai.github.io/langgraph/agents/context/)
- **Related Features**: This feature blocks all features in Phase 1 (003-006) and Phase 2 (007-009)
