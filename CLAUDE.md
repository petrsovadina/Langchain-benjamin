# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Czech MedAI (Benjamin)** je multi-agentní AI asistent pro české lékaře, postavený na LangGraph frameworku s Next.js frontenden a FastAPI bridge vrstvou. Systém poskytuje klinickou rozhodovací podporu integrující SÚKL, VZP, PubMed a ČLS JEP zdroje s inline citacemi.

## Architecture

Tři vrstvy, každá ve svém adresáři:

```
frontend/           → Next.js 14 (TypeScript, React 18, Tailwind v4, shadcn/ui)
langgraph-app/
  src/api/          → FastAPI bridge (SSE streaming, Redis cache, rate limiting)
  src/agent/        → LangGraph multi-agent graph (Python, async-first)
```

### Data Flow

```
Frontend (Next.js :3000)
  → POST /api/v1/consult (SSE stream)
    → FastAPI (:8000) with CORS, rate limiting, request ID tracking
      → LangGraph graph.ainvoke() / astream_events()
        → supervisor (LLM intent classification + Send API for parallel dispatch)
          → [drug_agent|pubmed_agent|guidelines_agent] → synthesizer
            → MCP servers (SÚKL-mcp, BioMCP)
      ← SSE events: agent_start → agent_complete → final → done
    ← StreamingResponse (text/event-stream)
  ← useConsult hook processes SSE → renders CitedResponse with [1][2][3] citations
```

### LangGraph State & Context Pattern

```python
@dataclass
class State:
    messages: Annotated[list[AnyMessage], add_messages]
    next: Annotated[str, _keep_last] = "__end__"
    retrieved_docs: Annotated[list[Document], add_documents] = field(default_factory=list)
    drug_query: DrugQuery | None = None
    research_query: ResearchQuery | None = None
    guideline_query: GuidelineQuery | None = None

class Context(TypedDict, total=False):
    model_name: str            # default: claude-sonnet-4-5-20250929
    temperature: float
    langsmith_project: str
    user_id: str | None
    sukl_mcp_client: Any       # SUKLMCPClient (Any for Pydantic compat)
    biomcp_client: Any         # BioMCPClient
    openai_api_key: str        # for guidelines embeddings
    conversation_context: Any  # ConversationContext
    mode: Literal["quick", "deep"]

# Node signature:
async def node_name(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
```

## Commands

### Backend (LangGraph + FastAPI)

All backend commands run from `langgraph-app/`:

```bash
# Setup
uv pip install -e .

# Dev server (LangGraph Studio)
./dev.sh                                    # or: PYTHONPATH=src langgraph dev

# FastAPI server
PYTHONPATH=src uvicorn api.main:app --host 0.0.0.0 --port 8000

# Tests
PYTHONPATH=src uv run pytest tests/unit_tests/ -v
PYTHONPATH=src uv run pytest tests/integration_tests/ -v
PYTHONPATH=src uv run pytest tests/unit_tests/nodes/test_pubmed_agent.py::TestPubMedSearch -v

# Code quality
uv run ruff format .
uv run ruff check .
uv run mypy --strict src/agent/

# All quality checks at once
uv run ruff format . && uv run ruff check . && uv run mypy --strict src/agent/

# Makefile shortcuts
make test                              # unit tests
make integration_tests                 # integration tests
make test TEST_FILE=tests/unit_tests/test_specific.py  # specific test
make test_watch                        # pytest watch mode
make lint                              # ruff + mypy --strict
make format                            # auto-format
make spell_check                       # codespell check
make spell_fix                         # codespell auto-fix
make lint_diff                         # lint only changed files vs main
```

**Note:** Makefile targets use `python -m pytest` without `PYTHONPATH=src`. Either activate `.venv` first or use the explicit `PYTHONPATH=src uv run pytest` commands above.

### Frontend

All frontend commands run from `frontend/`:

```bash
# Setup
npm install

# Dev server
npm run dev                             # Next.js on :3000

# Tests
npm test                                # Vitest unit tests
npm run test:watch                      # Vitest watch mode
npm run test:e2e                        # Playwright (Desktop Chrome, Mobile Chrome/Safari, Tablet)
npm run test:e2e:ui                     # Playwright UI mode

# Build & analysis
npm run build
npm run analyze                         # Bundle analyzer
npm run lighthouse                      # Lighthouse CI
```

### Docker (Production)

```bash
cd langgraph-app
docker compose up                       # API + Redis + PostgreSQL
```

## Code Conventions

### Python (backend)
- **mypy --strict** enforced - zero errors, no implicit `Any`
- Exception: `Any` with doc comment for MCP clients (Pydantic schema compat)
- Google-style docstrings
- `asyncio_mode = "auto"` in pyproject.toml - no `@pytest.mark.asyncio` decorator needed
- `AsyncMock` for MCP clients in tests
- `PYTHONPATH=src` always required (LangGraph CLI runs in pipx env)
- Node functions must be async with signature `(State, Runtime[Context]) -> dict[str, Any]`
- `get_mcp_clients(runtime)` in `graph.py` falls back to module-level clients when runtime context is empty - tests must `patch("agent.graph.get_mcp_clients")` to prevent leaking to real MCP servers

### TypeScript (frontend)
- Tailwind v4 with OKLCH semantic design tokens (no hardcoded colors)
- Use `bg-surface-elevated`, `text-primary` etc. instead of `bg-white dark:bg-slate-900`
- shadcn/ui components extended with `cva` variants (button: 10 sizes, badge: 6 variants)
- `@` path alias resolves to `frontend/` root
- Test with Vitest + React Testing Library + jest-axe (accessibility)

### Design Token System

CSS variables defined in `frontend/app/globals.css` using OKLCH color space:
- `--color-surface`, `--color-surface-elevated`, `--color-surface-muted`
- `--color-text-primary`, `--color-text-secondary`, `--color-text-tertiary`
- `--color-border-default`, `--color-border-focus`
- Citation-specific: `--citation-badge-hover`, `--citation-badge-active`

Light/dark themes auto-switch via `next-themes`. See `frontend/DESIGN_TOKENS.md` for reference.

## SSE Event Protocol

Frontend and backend communicate via Server-Sent Events:

| Event Type | Direction | Meaning |
|---|---|---|
| `agent_start` | backend → frontend | Agent begins processing (drug_agent, pubmed_agent, etc.) |
| `agent_complete` | backend → frontend | Agent finished |
| `final` | backend → frontend | Final answer + retrieved_docs + latency_ms |
| `done` | backend → frontend | Stream complete |
| `error` | backend → frontend | Error with detail message |
| `cache_hit` | backend → frontend | Response served from Redis cache (quick mode only) |

## Key Files

### Backend
- `langgraph-app/src/agent/graph.py` - Core graph (State, Context, route_query, compilation)
- `langgraph-app/src/agent/nodes/` - Node implementations (supervisor, drug_agent, pubmed_agent, guidelines_agent, general_agent, synthesizer, supervisor_prompts)
- `langgraph-app/src/agent/mcp/` - MCP clients: `adapters/` (SUKLMCPClient, BioMCPClient), `domain/` (ports, entities, exceptions)
- `langgraph-app/src/api/routes.py` - FastAPI endpoints (`/api/v1/consult`, `/health`)
- `langgraph-app/src/api/main.py` - FastAPI app (CORS, rate limiting, security headers)
- `langgraph-app/src/agent/models/` - Pydantic models (drug_models, research_models, guideline_models, supervisor_models)
- `langgraph-app/tests/conftest.py` - Pytest fixtures (mock_runtime, sample_state, sample_pubmed_articles)
- `langgraph-app/tests/unit_tests/` - Unit tests; also `tests/quality/`, `tests/load_tests/`, `tests/performance/`

### Frontend
- `frontend/app/page.tsx` - Main chat interface
- `frontend/app/globals.css` - Design tokens (OKLCH light/dark themes)
- `frontend/lib/api.ts` - SSE streaming client (`sendMessage` function)
- `frontend/lib/citations.ts` - Citation parsing & formatting
- `frontend/hooks/useConsult.ts` - API integration hook
- `frontend/components/Omnibox.tsx` - Medical query input
- `frontend/components/CitedResponse.tsx` - Response with inline citations
- `frontend/components/CitationBadge.tsx` - Citation [1] with HoverCard preview
- `frontend/vitest.config.ts` - Unit test config (jsdom, `@` alias)
- `frontend/playwright.config.ts` - E2E config (4 device profiles)

### Configuration
- `.specify/memory/constitution.md` - Project constitution v1.1.1 (5 principles + security standards)
- `specs/ROADMAP.md` - Master roadmap (12 features, 4 phases)
- `langgraph-app/.env` - Backend env vars (API keys, LangSmith)
- `frontend/.env.local` - Frontend env (`NEXT_PUBLIC_API_URL=http://localhost:8000`)

## Constitution (5 Principles)

Defined in `.specify/memory/constitution.md` v1.1.1:

1. **Graph-Centric Architecture** - All features as LangGraph nodes/edges, async functions
2. **Type Safety** - mypy --strict, typed dataclasses/TypedDict, zero errors
3. **Test-First Development** - Tests before implementation (TDD), target ≥80% coverage
4. **Observability** - LangSmith tracing, structured logging, LangGraph Studio debugging
5. **Modular Design** - Single responsibility per node, config in Context not hardcoded

## Environment Variables

### Backend (`langgraph-app/.env`)
```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...     # Supervisor + translation LLM calls
OPENAI_API_KEY=sk-...            # Guidelines embeddings (pgvector semantic search)

# MCP servers
SUKL_MCP_URL=...                 # SÚKL pharmaceutical DB
BIOMCP_COMMAND=...               # BioMCP REST client

# Infrastructure (docker-compose provides defaults)
DATABASE_URL=postgresql://...    # pgvector for guidelines
REDIS_URL=redis://localhost:6379 # Response cache

# Optional
LANGSMITH_API_KEY=lsv2_pt_...    # LangSmith tracing
LANGSMITH_PROJECT=czech-medai-dev
TRANSLATION_MODEL=claude-4.5-haiku
```

See `langgraph-app/.env.example` for complete variable reference with defaults.

### Frontend (`frontend/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Feature Development Workflow (SpecKit)

```bash
cd langgraph-app
make speckit_new FEATURE="Description"   # Create feature branch + spec
# Then in Claude Code:
# /speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

Specs live in `specs/NNN-feature-name/` with `spec.md`, `plan.md`, `tasks.md`.

## Docker Compose Services

`docker compose up` starts 3 services:
- **api** - FastAPI backend (port 8000, 4 uvicorn workers, non-root user)
- **redis** - Response cache (port 6379, 256MB max, allkeys-lru eviction)
- **postgres** - pgvector DB for guidelines (ankane/pgvector:latest)

Production uses `.env.production`. Health check: `GET /health`.

## API Middleware

- **Rate limiting**: 10 req/min per IP via slowapi
- **Request ID**: UUID per request in `X-Request-ID` header
- **Security headers**: HSTS, CSP, X-Frame-Options: DENY, nosniff
- **CORS**: Configurable via `CORS_ORIGINS` env var

## Troubleshooting

**`ModuleNotFoundError: No module named 'agent'`** - Use `./dev.sh` or prefix with `PYTHONPATH=src`.

**`uv run pytest` hangs on import** - Heavy dependency graph triggers MCP client init. Use `.venv/bin/pytest` with `PYTHONPATH=src` prefix instead, or ensure MCP servers are not expected at import time.

**Translation tests fail/skip** - 5 tests require `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`. Expected skips in local dev.

**Tests leak to real MCP servers** - Always `patch("agent.graph.get_mcp_clients")` in tests to prevent real MCP connections. See `tests/conftest.py` for patterns.

**Frontend can't connect to backend** - Ensure FastAPI runs on :8000 and `NEXT_PUBLIC_API_URL` is set in `frontend/.env.local`.

**Playwright tests fail on mock routes** - Mock routes must match `/api/v1/consult` (with version prefix), not `/api/consult`.

**Python version**: Dev uses 3.12 (langgraph.json), Docker uses 3.11, minimum is 3.10 (pyproject.toml).
