# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Czech MedAI (Benjamin)** je multi-agentní AI asistent pro české lékaře, postavený na LangGraph frameworku s Next.js frontendem a FastAPI bridge vrstvou. Systém poskytuje klinickou rozhodovací podporu integrující SÚKL, PubMed a ČLS JEP zdroje s inline citacemi.

## Architecture

Tři vrstvy:

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
      → LangGraph astream_events()
        → supervisor (LLM intent classification + Send API for parallel dispatch)
          → [drug_agent|pubmed_agent|guidelines_agent|general_agent] → synthesizer
            → MCP servers (SÚKL JSON-RPC, BioMCP REST)
      ← SSE events: agent_start → agent_complete → final → done
    ← StreamingResponse (text/event-stream)
  ← useConsult hook → CitedResponse with [1][2][3] citations
```

### Routing Architecture

Two-tier routing in supervisor:

1. **LLM Intent Classification** (primary) — Claude classifies into 8 intent types
2. **Keyword Fallback** — `fallback_to_keyword_routing()` in `supervisor.py` is the **single source of truth** for keyword matching

Priority: Drug > Research > Guidelines > General (default)

`route_query()` in `graph.py` delegates to `fallback_to_keyword_routing()` for keyword decisions (DRY).

### LangGraph State & Context

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
    model_name: str              # default: claude-sonnet-4-5-20250929
    temperature: float
    sukl_mcp_client: Any         # SUKLMCPClient (Any for Pydantic compat)
    biomcp_client: Any           # BioMCPClient
    mode: Literal["quick", "deep"]
    # ... see graph.py for full definition

# Node signature (all nodes follow this):
async def node_name(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
```

### Circular Import Pattern

All node modules use `TYPE_CHECKING` to avoid circular imports with `graph.py`:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langgraph.runtime import Runtime
    from agent.graph import Context, State
```

## Commands

### Backend (from `langgraph-app/`)

```bash
# Dev server (LangGraph Studio)
./dev.sh                                    # or: PYTHONPATH=src langgraph dev

# FastAPI server
PYTHONPATH=src uvicorn api.main:app --host 0.0.0.0 --port 8000

# Tests (PYTHONPATH=src required)
PYTHONPATH=src uv run pytest tests/unit_tests/ -v
PYTHONPATH=src uv run pytest tests/integration_tests/ -v
PYTHONPATH=src uv run pytest tests/unit_tests/nodes/test_supervisor.py::TestSupervisorNode -v

# Code quality
uv run ruff format . && uv run ruff check . && uv run mypy --strict src/agent/

# Makefile shortcuts
make test                              # unit tests
make lint                              # ruff + mypy --strict
make format                            # auto-format
make test TEST_FILE=tests/unit_tests/test_specific.py  # specific test
```

**Note:** Makefile targets use `python -m pytest` without `PYTHONPATH=src`. Either activate `.venv` first or use the explicit `PYTHONPATH=src uv run pytest` commands above.

### Frontend (from `frontend/`)

```bash
npm run dev                             # Next.js on :3000
npm test                                # Vitest unit tests
npm run test:e2e                        # Playwright (Desktop/Mobile Chrome, Safari, Tablet)
npm run build                           # Production build
```

### Docker

```bash
cd langgraph-app
docker compose up                       # API (8000) + Redis (6379) + PostgreSQL/pgvector (5432)
```

## Code Conventions

### Python (backend)
- **mypy --strict** — zero errors, no implicit `Any`
- Exception: `Any` with doc comment for MCP clients in Context (Pydantic schema compat)
- Google-style docstrings required for all nodes
- `asyncio_mode = "auto"` in pyproject.toml — no `@pytest.mark.asyncio` needed
- `PYTHONPATH=src` always required (LangGraph CLI runs in pipx env)
- All agent nodes live in `src/agent/nodes/` as separate modules
- `get_mcp_clients(runtime)` in `graph.py` — tests must `patch("agent.graph.get_mcp_clients")` to prevent real MCP connections
- MCP clients use `AsyncMock` in tests, `IMCPClient` interface from `agent.mcp.domain.ports`

### TypeScript (frontend)
- Tailwind v4 with OKLCH semantic design tokens — use `bg-surface-elevated`, `text-primary` etc.
- shadcn/ui components extended with `cva` variants
- `@` path alias resolves to `frontend/` root
- Test with Vitest + React Testing Library + jest-axe (accessibility)
- Design token reference: `frontend/DESIGN_TOKENS.md`

## SSE Event Protocol

| Event Type | Meaning |
|---|---|
| `agent_start` | Agent begins processing (drug_agent, pubmed_agent, guidelines_agent, general_agent) |
| `agent_complete` | Agent finished |
| `cache_hit` | Response served from Redis cache (quick mode only) |
| `final` | Final answer + retrieved_docs + latency_ms |
| `done` | Stream complete |
| `error` | Error with detail message |

## Key Files

### Backend
- `src/agent/graph.py` — State, Context, route_query, keyword sets, graph compilation
- `src/agent/nodes/` — supervisor, drug_agent, pubmed_agent, guidelines_agent, general_agent, synthesizer
- `src/agent/mcp/` — `adapters/` (SUKLMCPClient, BioMCPClient), `domain/` (IMCPClient port, entities, exceptions)
- `src/api/routes.py` — `/api/v1/consult` (SSE), `/health`
- `src/api/main.py` — CORS, rate limiting (10/min), security headers, request ID middleware
- `src/agent/models/` — Pydantic models (DrugQuery, ResearchQuery, GuidelineQuery, IntentResult)
- `tests/conftest.py` — shared fixtures (mock_runtime, sample_state)

### Frontend
- `app/page.tsx` — main chat interface
- `lib/api.ts` — SSE streaming client
- `hooks/useConsult.ts` — API integration hook with retry
- `components/CitedResponse.tsx` + `CitationBadge.tsx` — citation rendering

### Governance
- `.specify/memory/constitution.md` — Project constitution v1.1.2 (5 principles + security standards)
- `specs/ROADMAP.md` — Master roadmap (12 features, 4 phases)

## Constitution (5 Principles)

Defined in `.specify/memory/constitution.md` v1.1.2:

1. **Graph-Centric Architecture** — All features as LangGraph nodes/edges, Send API routing
2. **Type Safety** — mypy --strict, typed dataclasses/TypedDict, zero errors
3. **Test-First Development** — Tests before implementation (TDD), 442/442 passing
4. **Observability** — LangSmith tracing, structured logging, specific exception types
5. **Modular Design** — Single responsibility per node in `nodes/`, IMCPClient interface, config in Context

## Environment Variables

### Backend (`langgraph-app/.env`)
```bash
ANTHROPIC_API_KEY=sk-ant-...     # Required: supervisor + agent LLM calls
OPENAI_API_KEY=sk-...            # Guidelines embeddings (pgvector)
SUKL_MCP_URL=...                 # SÚKL MCP server
BIOMCP_COMMAND=...               # BioMCP REST client
DATABASE_URL=postgresql://...    # pgvector for guidelines
REDIS_URL=redis://localhost:6379 # Response cache
LANGSMITH_API_KEY=lsv2_pt_...    # Optional: LangSmith tracing
```

See `langgraph-app/.env.example` for complete reference with defaults.

### Frontend (`frontend/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Troubleshooting

**`ModuleNotFoundError: No module named 'agent'`** — Use `./dev.sh` or prefix with `PYTHONPATH=src`.

**`uv run pytest` hangs on import** — Heavy dependency graph triggers MCP client init. Use `PYTHONPATH=src uv run pytest` or `.venv/bin/pytest` with `PYTHONPATH=src`.

**Tests leak to real MCP servers** — Always `patch("agent.graph.get_mcp_clients")` in tests. See `tests/conftest.py`.

**Translation tests skip** — 5 tests require `ANTHROPIC_API_KEY` in `.env`. Expected in local dev.

**Playwright mock routes** — Must match `/api/v1/consult` (with version prefix), not `/api/consult`.

**Python version** — Dev: 3.12, Docker: 3.11, minimum: 3.10 (pyproject.toml).
