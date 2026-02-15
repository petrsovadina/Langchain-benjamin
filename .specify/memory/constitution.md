<!--
SYNC IMPACT REPORT:
- Version change: 1.1.1 → 1.1.2 (PATCH)
- Bump rationale: Routing architecture section updated to reflect DRY
  consolidation (route_query delegates to fallback_to_keyword_routing).
  Test metrics updated after AGENT_TO_NODE_MAP test removal.
  Node structure clarification (all agents in nodes/).
- Modified principles: None (all 5 principles unchanged)
- Enhanced sections:
  * Routing Architecture: Updated delegation model description
  * Testing: Updated test metrics to 442/442 = 100% (post-refactoring)
  * Principle V rationale: Added node location convention
- Added sections: None
- Removed sections: None
- Templates requiring updates:
  ✅ plan-template.md - No changes needed (Principle references intact)
  ✅ spec-template.md - No changes needed
  ✅ tasks-template.md - No changes needed (node paths advisory, not prescriptive)
  ✅ checklist-template.md - No changes needed
- Follow-up TODOs: None
- Change context:
  * Refactoring session: 8 changes applied (see commit on branch `new`)
  * general_agent_node extracted from graph.py → nodes/general_agent.py
  * route_query() now delegates to fallback_to_keyword_routing() (DRY)
  * AGENT_TO_NODE_MAP removed (identity map, no functional purpose)
  * Dead code __post_init__ removed from State dataclass
  * DRY helpers: _parse_drug_result, _build_terminology_warning,
    _extract_message_content_raw
  * Bugfix: general_agent added to SSE event filters in routes.py
  * Test suite: 442 passed, 0 failed

PREVIOUS REPORT (1.1.0 → 1.1.1):
- Corrected stale test metrics and fixed translation test count (6 → 5)
- Test suite: 444 passed, 5 skipped (translation tests requiring API credits)

PREVIOUS REPORT (1.0.4 → 1.1.0):
- Materially expanded guidance - added Security Standards, Frontend Tech Stack,
  MCP Protocol
- Test coverage improved: 177/183 → 444/449 (98.9%)
- 12 new tests added (4 routing regression + 8 security)
- Security hardening: thread-safe IDs, size limits, async context manager,
  ReDoS-safe regex
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
- Routing MUST use the Send API for dynamic multi-agent dispatch

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
- **Regression tests**: Cover routing priority changes and security fixes
- Test workflow: Write test → Verify it fails → Implement → Verify it passes
- Use `pytest` as testing framework (already configured in pyproject.toml)
- Contract tests for external API integrations when applicable

**Rationale**: LangGraph agents are complex state machines. Test-first ensures each node behaves correctly in isolation and composition before deployment.

### IV. Observability & Debugging

**ALL graph executions MUST be traceable**.

- Enable LangSmith tracing via `.env` configuration (`LANGSMITH_API_KEY`)
- Use structured `logging` module (not `print()`) for production code
- Node implementations MUST log key decisions and data transformations
- Use LangGraph Studio for visual debugging during development
- Checkpoint state before/after complex operations
- Exception handlers MUST use specific exception types (not bare `except Exception`)

**Rationale**: Agent debugging is impossible without execution traces. LangSmith and Studio provide the tooling; adherence to logging practices makes them effective.

### V. Modular & Extensible Design

**Keep nodes small, focused, and composable**.

- Each node MUST have a single, clear responsibility
- Prefer multiple small nodes over one large node
- All agent nodes MUST reside in `src/agent/nodes/` as separate modules
- Extract reusable logic into helper functions in `src/agent/` modules
- Use subgraphs for complex multi-step operations
- Configuration parameters MUST go in `Context`, not hardcoded
- MCP clients MUST implement `IMCPClient` interface and support async context manager (`__aenter__`/`__aexit__`)

**Rationale**: Small nodes are easier to test, debug, and reuse. LangGraph supports composition; leverage it for maintainability. Separate modules per agent enable independent testing and clear ownership.

## Technology Stack

### Backend Mandatory Technologies

- **Python**: >=3.10 (as per pyproject.toml)
- **LangGraph**: >=1.0.0 (core framework)
- **LangGraph CLI**: For local development server (`langgraph dev`)
- **FastAPI**: Bridge layer for SSE streaming (`src/api/`)
- **pytest**: Testing framework with conftest.py fixtures
- **ruff**: Linting and formatting (configured in pyproject.toml)
- **mypy**: Type checking with --strict mode enforcement

### Frontend Mandatory Technologies

- **Next.js**: 14 (React 18, App Router)
- **TypeScript**: Strict mode
- **Tailwind CSS**: v4 with OKLCH semantic design tokens
- **shadcn/ui**: Component library extended with `cva` variants
- **Vitest**: Unit testing with React Testing Library + jest-axe
- **Playwright**: E2E testing (Desktop Chrome, Mobile Chrome/Safari, Tablet)

### MCP Protocol Standards

MCP (Model Context Protocol) clients communicate with external data sources:

- **SUKL MCP**: JSON-RPC 2.0 protocol (Czech pharmaceutical database)
- **BioMCP**: REST protocol (PubMed/biomedical literature)
- Protocol choice is per-server (not a project-wide decision)
- All MCP clients MUST implement `IMCPClient` interface from `agent.mcp.interfaces`
- JSON-RPC requests MUST use `_build_rpc_request()` DRY helper pattern

### Recommended Integrations

- **LangSmith**: Tracing and monitoring (via `LANGSMITH_API_KEY`)
- **python-dotenv**: Environment variable management
- **LangGraph Studio**: Visual debugging and development
- **Redis**: Response caching for quick mode

### Constraints

- **No direct database ORM**: Use LangGraph checkpointing for persistence
- **Async-first**: All node functions must be `async def`
- **Minimal external dependencies**: Justify new dependencies against core LangGraph patterns

## Security Standards

### Input Validation

- All external input MUST be validated at system boundaries
- Content size MUST be bounded (`MAX_CONTENT_SIZE` for HTTP responses, `MAX_TEXT_LENGTH` for parsed text)
- Regex patterns MUST be line-anchored to prevent ReDoS attacks
- JSON parsing MUST catch `RecursionError` for deeply nested payloads

### Thread Safety

- Shared mutable counters MUST use `itertools.count()` or `threading.Lock`
- Request ID generation MUST be thread-safe (no `self._id += 1` pattern)

### Resource Management

- HTTP clients MUST implement async context manager (`__aenter__`/`__aexit__`)
- Sessions MUST be set to `None` on close to prevent stale references
- Timeouts MUST be configured for all external HTTP calls

### Exception Handling

- Catch specific exception types, not bare `except Exception`
- Network errors: `aiohttp.ClientError`, `TimeoutError`, `OSError`
- Parse errors: `ValueError`, `KeyError`, `TypeError`
- Use `logger.exception()` for unexpected errors (preserves traceback)
- Use `logger.warning()` for expected fallback scenarios
- All external-facing functions MUST have fallback behavior (graceful degradation)

## Development Workflow

### Feature Development Process

1. **Specify** (`/speckit.specify`): Define user stories with acceptance criteria
2. **Plan** (`/speckit.plan`): Design graph nodes, edges, state schema changes
3. **Clarify** (`/speckit.clarify`): Resolve ambiguities before implementation
4. **Tasks** (`/speckit.tasks`): Break down into atomic, testable tasks
5. **Implement** (`/speckit.implement`): Execute tasks with test-first approach
6. **Validate**: Run tests, verify in LangGraph Studio, check traces in LangSmith

### Code Quality Gates

All code MUST pass these enforced quality checks before merge:

#### Type Checking
- **mypy --strict**: Zero errors required
  ```bash
  mypy --strict src/agent/nodes/your_node.py
  ```
- All function signatures MUST have complete type hints
- No `Any` types without documented justification (see Principle II exception)

#### Linting & Formatting
- **ruff format**: Auto-format all Python files
  ```bash
  ruff format .
  ```
- **ruff check**: All checks MUST pass
  ```bash
  ruff check .
  ```
- Enabled rules: E (pycodestyle), F (pyflakes), I (isort), D (pydocstyle), D401, T201, UP
- Per-file ignores configured in `pyproject.toml`:
  - `tests/*`: D (docstrings), UP (modernization), T201 (print)
  - `src/*`: T201 (print allowed for debugging/logging)

#### Documentation
- **Docstrings REQUIRED** for all nodes (Google-style convention)
- Format: Summary line, blank line, Args, Returns, Raises (if applicable), Example
- Use `r"""` prefix if docstring contains backslashes

#### Testing
- **Test coverage**: Minimum 80% for node implementations (current: 442/442 = 100%)
- All tests MUST pass: `pytest tests/`
- Note: 5 translation tests require API credits (expected skip without ANTHROPIC_API_KEY)
- Performance benchmarks for latency-critical nodes
- Regression tests MUST accompany routing priority or keyword changes

#### Package Configuration
- Use `[tool.setuptools.packages.find]` in pyproject.toml for package discovery
- Ensure `agent` package is importable from `src/` directory structure

### Version Control

- **Feature branches**: Use format `###-feature-name` (e.g., `001-rag-pipeline`)
- **Commits**: Conventional format (`feat:`, `fix:`, `test:`, `docs:`)
- **Pull requests**: Must pass all tests and linting before merge

## Routing Architecture

### Priority Order (codified 2026-02-09, consolidated 2026-02-15)

Query routing follows this strict priority (highest to lowest):

1. **Explicit queries**: `drug_query`, `research_query`, `guideline_query` in State
2. **Drug keywords**: Most common use case (SUKL database)
3. **Research keywords**: Research-specific terms only (`studie`, `vyzkum`, `pubmed`)
4. **Guidelines keywords**: Clinical guidelines (`doporucene postupy`, `standardy`, `ESC`)
5. **General agent**: Fallback for unmatched queries

### Single Source of Truth

`fallback_to_keyword_routing()` in `supervisor.py` is the canonical keyword routing implementation. `route_query()` in `graph.py` delegates to it for keyword-based decisions (after checking explicit queries). This eliminates duplicate keyword logic and ensures both paths always agree.

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
- Security standards MUST be verified during code review

**Version**: 1.1.2 | **Ratified**: 2026-01-13 | **Last Amended**: 2026-02-15
