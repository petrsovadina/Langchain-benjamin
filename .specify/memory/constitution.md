<!--
SYNC IMPACT REPORT:
- Version change: 1.0.1 → 1.0.2 (PATCH)
- Bump rationale: Added pragmatic workaround pattern for Pydantic schema generation in Context TypedDict
- Modified principles:
  * Principle II (Type Safety): Added exception clause for LangGraph Context schema compatibility
- Added sections: None
- Removed sections: None
- Templates requiring updates:
  ✅ plan-template.md - Verified aligned (Constitution Check reference unchanged)
  ✅ spec-template.md - Verified aligned (no impact on spec structure)
  ✅ tasks-template.md - Verified aligned (TDD workflow intact)
- Follow-up TODOs: None
- Change context:
  * Recent integration (Feature 003) revealed Pydantic schema generation failure when Context TypedDict
    used strict types for MCP clients (SUKLMCPClient, BioMCPClient) under TYPE_CHECKING
  * Workaround: Use `Any` type annotation with documentation comment explaining actual type
  * Commits: d83323f (Pydantic fix), b364c5c (routing integration)
  * This is a pragmatic exception, not a weakening of type safety principle
-->

# Langchain-Benjamin Constitution

## Core Principles

### I. Graph-Centric Architecture

**ALL features MUST be implemented as LangGraph nodes and edges**.

- Every feature extends the state graph in `src/agent/graph.py`
- Node functions MUST be async and follow signature: `async def node_name(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- State transitions MUST be explicit via `.add_edge()` or conditional edges
- No business logic outside of graph nodes (keep controllers, helpers minimal)
- Graph structure MUST be visualizable in LangGraph Studio

**Rationale**: LangGraph is the orchestration backbone. Maintaining graph-centric design ensures debuggability, traceability, and visual comprehension of agent behavior.

### II. Type Safety & Schema Validation

**ALL state and context MUST use typed dataclasses/TypedDict**.

- `State` dataclass defines all graph state fields with type hints
- `Context` TypedDict defines all runtime configuration parameters
- No dynamic attributes or untyped dictionaries in state/context
- Input/output of nodes MUST return `Dict[str, Any]` matching State fields
- Use Pydantic models for external data validation where appropriate

**Exception**: When TypedDict types cause Pydantic schema generation failures (e.g., in LangGraph Context):
- Use `Any` type annotation with documentation comment explaining actual type
- Example: `sukl_mcp_client: Any  # Actual type: SUKLMCPClient (from agent.mcp)`
- This preserves runtime type checking while allowing LangGraph Studio schema introspection

**Rationale**: Type safety prevents runtime errors, enables IDE autocomplete, and makes state evolution trackable. LangGraph requires strict typing for state management, but Pydantic schema generation has limitations with complex forward-referenced types.

### III. Test-First Development (NON-NEGOTIABLE)

**Tests MUST be written before implementation**.

- **Unit tests**: Cover individual node logic in `tests/unit_tests/`
- **Integration tests**: Validate full graph execution in `tests/integration_tests/`
- Test workflow: Write test → Verify it fails → Implement → Verify it passes
- Use `pytest` as testing framework (already configured in pyproject.toml)
- Contract tests for external API integrations when applicable

**Rationale**: LangGraph agents are complex state machines. Test-first ensures each node behaves correctly in isolation and composition before deployment.

### IV. Observability & Debugging

**ALL graph executions MUST be traceable**.

- Enable LangSmith tracing via `.env` configuration (`LANGSMITH_API_KEY`)
- Log state transitions at node boundaries (use `print()` or structured logging)
- Node implementations MUST log key decisions and data transformations
- Use LangGraph Studio for visual debugging during development
- Checkpoint state before/after complex operations

**Rationale**: Agent debugging is impossible without execution traces. LangSmith and Studio provide the tooling; adherence to logging practices makes them effective.

### V. Modular & Extensible Design

**Keep nodes small, focused, and composable**.

- Each node MUST have a single, clear responsibility
- Prefer multiple small nodes over one large node
- Extract reusable logic into helper functions in `src/agent/` modules
- Use subgraphs for complex multi-step operations
- Configuration parameters MUST go in `Context`, not hardcoded

**Rationale**: Small nodes are easier to test, debug, and reuse. LangGraph supports composition; leverage it for maintainability.

## Technology Stack

### Mandatory Technologies

- **Python**: ≥3.10 (as per pyproject.toml)
- **LangGraph**: ≥1.0.0 (core framework)
- **LangGraph CLI**: For local development server (`langgraph dev`)
- **pytest**: Testing framework with conftest.py fixtures
- **ruff**: Linting and formatting (configured in pyproject.toml)
- **mypy**: Type checking (optional-dev dependency)

### Recommended Integrations

- **LangSmith**: Tracing and monitoring (via `LANGSMITH_API_KEY`)
- **python-dotenv**: Environment variable management
- **LangGraph Studio**: Visual debugging and development

### Constraints

- **No direct database ORM**: Use LangGraph checkpointing for persistence
- **Async-first**: All node functions must be `async def`
- **Minimal external dependencies**: Justify new dependencies against core LangGraph patterns

## Development Workflow

### Feature Development Process

1. **Specify** (`/speckit.specify`): Define user stories with acceptance criteria
2. **Plan** (`/speckit.plan`): Design graph nodes, edges, state schema changes
3. **Clarify** (`/speckit.clarify`): Resolve ambiguities before implementation
4. **Tasks** (`/speckit.tasks`): Break down into atomic, testable tasks
5. **Implement** (`/speckit.implement`): Execute tasks with test-first approach
6. **Validate**: Run tests, verify in LangGraph Studio, check traces in LangSmith

### Code Quality Gates

- **ALL code MUST pass `ruff` linting** (E, F, I, D, D401, T201, UP rules)
- **Type hints REQUIRED** on all function signatures (enforced by mypy)
- **Docstrings REQUIRED** for all nodes (Google-style convention)
- **Test coverage**: Minimum 80% for node implementations
- **Graph visualization**: Feature must render correctly in Studio

### Version Control

- **Feature branches**: Use format `###-feature-name` (e.g., `001-rag-pipeline`)
- **Commits**: Conventional format (`feat:`, `fix:`, `test:`, `docs:`)
- **Pull requests**: Must pass all tests and linting before merge

## Governance

### Amendment Process

This constitution is a living document. Amendments require:

1. Documented justification for change (why current principle insufficient)
2. Impact analysis on existing code and templates
3. Update to constitution version (semantic versioning: MAJOR.MINOR.PATCH)
4. Synchronization of dependent templates (plan, spec, tasks)

### Versioning Policy

- **MAJOR**: Principle removal or backward-incompatible redefinition
- **MINOR**: New principle added or significant principle expansion
- **PATCH**: Clarifications, typo fixes, non-semantic refinements

### Compliance

- All features MUST reference constitution principles in plan.md "Constitution Check" section
- Violations (e.g., adding non-graph logic) MUST be justified in "Complexity Tracking" table
- Use `.specify/memory/constitution.md` as single source of truth for development standards

**Version**: 1.0.2 | **Ratified**: 2026-01-13 | **Last Amended**: 2026-01-20
