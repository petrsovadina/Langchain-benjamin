<!--
SYNC IMPACT REPORT:
- Version change: 1.2.1 → 1.3.0 (MINOR)
- Bump rationale: Materially expanded Security Standards with 4 new
  subsections based on comprehensive security audit (2026-03-12).
  Added Production Readiness Standards section. Updated test metrics
  to reflect translation test mock fix. This is a MINOR bump because
  new mandatory requirements are added.
- Modified principles: None (all 5 principles unchanged)
- Enhanced sections:
  * Security Standards — 4 new subsections: Error Response Sanitization,
    CORS Policy, LLM Client Configuration, Cache Security
  * Technology Stack — Test metrics corrected, translation test note updated
  * Routing Architecture — Added known issues subsection
- Added sections:
  * Production Readiness Standards (auth, config management, Docker)
- Removed sections: None
- Templates requiring updates:
  ✅ plan-template.md — No changes needed (Constitution Check references
     principles I-V which are unchanged)
  ✅ spec-template.md — No changes needed
  ✅ tasks-template.md — No changes needed (security hardening phase
     already exists as "Phase N: Polish & Cross-Cutting")
  ✅ checklist-template.md — No changes needed
- Follow-up TODOs:
  * Implement API key authentication (constitution now mandates it)
  * Add startup CORS validation for production environment
  * Set LLM timeout to ≤60s on all ChatAnthropic instances
  * Use full SHA-256 hash for cache keys
  * Centralize agent-layer configuration into validated Settings class

PREVIOUS REPORT (1.2.0 → 1.2.1):
- Test metrics corrected from 442/442 to 444/449 after validation run.
  5 translation tests fail due to unmocked LLM calls (known bug).

PREVIOUS REPORT (1.1.2 → 1.2.0):
- Supabase migration introduces asyncpg as mandatory backend technology.
  Guidelines storage uses direct asyncpg to Supabase PostgreSQL with pgvector.

PREVIOUS REPORT (1.1.1 → 1.1.2):
- Routing architecture section updated to reflect DRY consolidation.

PREVIOUS REPORT (1.1.0 → 1.1.1):
- Corrected stale test metrics and fixed translation test count.

PREVIOUS REPORT (1.0.4 → 1.1.0):
- Materially expanded guidance — added Security Standards, Frontend
  Tech Stack, MCP Protocol. 12 new tests added.
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
- **asyncpg**: Direct async PostgreSQL access for application data (guidelines storage with pgvector)
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

- **Supabase**: Managed PostgreSQL platform (pgvector, auth, storage)
- **LangSmith**: Tracing and monitoring (via `LANGSMITH_API_KEY`)
- **python-dotenv**: Environment variable management
- **LangGraph Studio**: Visual debugging and development
- **Redis**: Response caching for quick mode

### Constraints

- **Dual persistence model**: LangGraph checkpointing handles graph state; application data (e.g., guidelines with embeddings) uses asyncpg to Supabase PostgreSQL. No ORM layer — use raw asyncpg queries.
- **Async-first**: All node functions must be `async def`
- **Minimal external dependencies**: Justify new dependencies against core LangGraph patterns

## Security Standards

### Input Validation

- All external input MUST be validated at system boundaries
- Content size MUST be bounded (`MAX_CONTENT_SIZE` for HTTP responses, `MAX_TEXT_LENGTH` for parsed text)
- Regex patterns MUST be line-anchored to prevent ReDoS attacks
- JSON parsing MUST catch `RecursionError` for deeply nested payloads
- User-supplied identifiers (e.g., `user_id`) MUST be validated for format, length, and character set before use in logs or context

### Error Response Sanitization

- External-facing error responses MUST NOT expose internal implementation details
- SSE stream error events MUST use generic messages in production: `"An unexpected error occurred"`
- Raw exception messages (`str(e)`) MUST only be sent to clients when `settings.environment != "production"`
- Health endpoint status fields MUST NOT expose raw database or connection error details to unauthenticated callers
- All errors MUST be logged server-side with full detail (`logger.error(..., exc_info=True)`) regardless of what is sent to clients

### CORS Policy

- `allow_origins` MUST NOT fall back to `["*"]` in production
- Application MUST validate at startup that `cors_origins` is non-empty when `environment == "production"` and fail fast if not
- `allow_credentials=True` MUST NOT be combined with wildcard origins
- Development environments MAY use `["*"]` origins with explicit environment check

### LLM Client Configuration

- All `ChatAnthropic` instances MUST set an explicit `timeout` value (≤60 seconds)
- `timeout=None` is PROHIBITED — it disables per-call timeout and creates DoS risk even when outer `asyncio.timeout` is present
- LLM instances SHOULD be reused across requests where model parameters are identical, rather than instantiated per-request

### Cache Security

- Cache keys MUST use the full cryptographic hash digest (not truncated)
- SHA-256 truncation to <32 characters is PROHIBITED for medical query caching due to collision risk in patient-safety-critical context
- Cache invalidation MUST use `SCAN` pattern, not `KEYS *` (which is O(n) and blocks Redis)

### Thread Safety

- Shared mutable counters MUST use `itertools.count()` or `threading.Lock`
- Request ID generation MUST be thread-safe (no `self._id += 1` pattern)

### Resource Management

- HTTP clients MUST implement async context manager (`__aenter__`/`__aexit__`)
- Sessions MUST be set to `None` on close to prevent stale references
- Timeouts MUST be configured for all external HTTP calls
- Database connections MUST use connection pools with bounded size

### Exception Handling

- Catch specific exception types, not bare `except Exception`
- Network errors: `aiohttp.ClientError`, `TimeoutError`, `OSError`
- Database errors: `asyncpg.PostgresError`, `asyncpg.InterfaceError`
- Parse errors: `ValueError`, `KeyError`, `TypeError`
- Use `logger.exception()` for unexpected errors (preserves traceback)
- Use `logger.warning()` for expected fallback scenarios
- All external-facing functions MUST have fallback behavior (graceful degradation)

### Privacy & Data Protection

- Medical query content MUST NOT be logged at INFO level; use DEBUG or hash the content for correlation
- LangSmith tracing sends full query content to a third-party service; `LANGSMITH_TRACING` MUST default to `false` in `.env.example`
- Log fields containing user-supplied data MUST be sanitized to prevent log injection (newlines, JSON-breaking characters)

## Production Readiness Standards

### Authentication

- All data-mutating and LLM-consuming endpoints MUST require authentication before public deployment
- At minimum, API key authentication MUST be implemented on `/api/v1/consult`
- The `jwt_secret` configuration field in `Settings` MUST be utilized or removed (no dead config)
- `user_id` MUST be bound to authenticated identity, not accepted from unauthenticated client input

### Configuration Management

- The API layer (`src/api/`) MUST use `pydantic-settings` `BaseSettings` for all configuration
- The agent layer (`src/agent/`) MUST NOT use ad-hoc `os.getenv()` calls for configuration; a validated configuration class MUST be used
- Environment variable defaults MUST be safe for production (no `["*"]` CORS, no disabled auth)
- Project version MUST be consistent across `pyproject.toml`, API metadata, and `Settings`

### Docker & Deployment

- Docker Compose MUST NOT contain hardcoded database credentials in `environment:` blocks
- All secrets MUST be provided via `env_file` or environment injection, not inline YAML
- Redis MUST require authentication (`--requirepass`) in production
- Database and cache ports MUST NOT be exposed to `0.0.0.0` in production Compose profiles
- Docker images MUST use non-root users (already implemented via `appuser`)

### Dependency Management

- A lock file (`uv.lock`) MUST be committed for reproducible builds
- `[project.optional-dependencies]` and `[dependency-groups]` MUST NOT define the same tool with different versions
- Unused dependencies MUST be removed (e.g., `sse-starlette` if not imported)

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
- **Test coverage**: Minimum 80% for node implementations (current: 449/449 unit tests passing, 89 integration tests)
- All tests MUST pass: `pytest tests/`
- Translation tests now use `_mock_llm()` context manager — no live LLM calls required
- Performance benchmarks for latency-critical nodes
- Regression tests MUST accompany routing priority or keyword changes
- Stub/placeholder tests (e.g., `assert isinstance(graph, Pregel)`) MUST be replaced with behavioral tests or removed

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

### Known Issues (as of 2026-03-12 audit)

- `RESEARCH_KEYWORDS` is duplicated between `graph.py` and `pubmed_agent.py` with diverging sets — MUST be consolidated
- `source_filter` parameter in `guidelines_storage.py` is silently replaced with hardcoded `"guidelines"` regardless of input — the API is misleading
- `State.next` field is populated by every agent node but never read by graph routing — dead code that SHOULD be removed

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
- Production readiness standards MUST be verified before any public deployment

**Version**: 1.3.0 | **Ratified**: 2026-01-13 | **Last Amended**: 2026-03-12
