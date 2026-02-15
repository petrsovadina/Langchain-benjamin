# Czech MedAI (Benjamin)

Multi-agentní AI asistent pro české lékaře postavený na LangGraph frameworku s Next.js frontendem a FastAPI bridge vrstvou. Poskytuje klinickou rozhodovací podporu založenou na důkazech, integrující specializované AI agenty pro dotazování českých medicínských zdrojů (SÚKL, VZP, ČLS JEP) a mezinárodního výzkumu (PubMed) s kompletním sledováním citací.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/petrsovadina/Langchain-benjamin.git
cd Langchain-benjamin

# 2. Backend setup
cd langgraph-app
uv venv && source .venv/bin/activate
uv pip install -e .
uv pip install 'langgraph-cli[inmem]'
cp .env.example .env    # Editujte: ANTHROPIC_API_KEY, OPENAI_API_KEY (guidelines), LANGSMITH_API_KEY (optional)

# 3. Spustit backend
./dev.sh                # LangGraph Studio na http://127.0.0.1:2024
# NEBO pro FastAPI server:
PYTHONPATH=src uvicorn api.main:app --host 0.0.0.0 --port 8000

# 4. Frontend setup (v novém terminálu)
cd frontend
npm install
npm run dev             # Next.js na http://localhost:3000
```

> **PYTHONPATH**: Backend vyžaduje `PYTHONPATH=src` - script `dev.sh` to nastavuje automaticky.

**Detailní návod:** [QUICKSTART.md](./QUICKSTART.md)

## Architektura

### Multi-Agent Pattern

```
User Query (CZ)
    |
[Supervisor Node] → LLM intent classification (8 typů) + Send API
    |
    |--→ [Drug Agent] → SÚKL-mcp (9 MCP tools, 68k+ léků)
    |--→ [PubMed Agent] → BioMCP (24 tools)
    |      └→ Interní CZ→EN překlad dotazu před BioMCP voláním
    |--→ [Guidelines Agent] → ČLS JEP PDFs (pgvector)
    |--→ [General Agent] → Obecné medicínské dotazy (Claude LLM)
    |
[Synthesizer Node] → Kombinace + formátování + inline citace [1][2][3]
    |
Response (CZ)
```

### Tři vrstvy

```
frontend/           → Next.js 14 (TypeScript, React 18, Tailwind v4, shadcn/ui)
langgraph-app/
  src/api/          → FastAPI bridge (SSE streaming, Redis cache, rate limiting)
  src/agent/        → LangGraph multi-agent graph (Python, async-first)
```

### Frontend ↔ Backend komunikace (SSE)

Frontend a backend komunikují přes Server-Sent Events na `POST /api/v1/consult`:

| Event | Význam |
|---|---|
| `agent_start` | Agent začíná zpracování |
| `agent_complete` | Agent dokončil |
| `final` | Finální odpověď + citace + latency_ms |
| `done` | Stream ukončen |
| `error` | Chyba s detailem |
| `cache_hit` | Odpověď z Redis cache (quick mode) |

### Tech Stack

| Vrstva | Technologie |
|---|---|
| **Frontend** | Next.js 14, React 18, TypeScript, Tailwind v4, shadcn/ui, OKLCH design tokens |
| **API Bridge** | FastAPI, SSE streaming, Redis cache, slowapi rate limiting |
| **Orchestrace** | LangGraph ≥1.0.0, Python ≥3.10, async-first |
| **Data** | MCP protocol (SÚKL-mcp, BioMCP), pgvector, Supabase |
| **Kvalita** | mypy --strict, ruff, Vitest, Playwright, pytest |
| **Observability** | LangSmith tracing, structured JSON logging |
| **MCP Servery** | [SÚKL-mcp](https://github.com/petrsovadina/SUKL-mcp), [BioMCP](https://github.com/genomoncology/biomcp) |

## Development

### Backend (z `langgraph-app/`)

```bash
./dev.sh                     # Dev server (LangGraph Studio)
make test                    # Unit testy
make integration_tests       # Integrační testy
make test TEST_FILE=tests/unit_tests/test_specific.py  # Konkrétní test
make lint                    # ruff + mypy --strict
make format                  # Auto-format
```

### Frontend (z `frontend/`)

```bash
npm run dev                  # Next.js na :3000
npm test                     # Vitest unit testy
npm run test:e2e             # Playwright (Desktop/Mobile Chrome, Safari, Tablet)
npm run test:e2e:ui          # Playwright UI mode
npm run build                # Production build
npm run analyze              # Bundle analyzer
```

### Docker (Production)

```bash
cd langgraph-app
docker compose up            # API + Redis + PostgreSQL
```

## Struktura Projektu

```
Langchain-benjamin/
├── CLAUDE.md                  # Guide pro Claude Code instances
├── QUICKSTART.md              # Rychlý start guide
├── frontend/                  # Next.js 14 frontend
│   ├── app/page.tsx           # Hlavní chat interface
│   ├── app/globals.css        # OKLCH design tokens (light/dark)
│   ├── components/            # 14 React komponent (Omnibox, CitedResponse, ...)
│   ├── hooks/                 # useConsult, useOnlineStatus, useSwipeGesture
│   ├── lib/                   # api.ts (SSE client), citations.ts
│   └── e2e/                   # Playwright E2E testy
├── langgraph-app/             # Python backend
│   ├── src/agent/graph.py     # Core LangGraph graph (State, Context, nodes)
│   ├── src/agent/nodes/       # supervisor, drug_agent, pubmed_agent, guidelines_agent, general_agent, synthesizer
│   ├── src/agent/mcp/         # MCP client wrappers (SÚKL, BioMCP)
│   ├── src/agent/models/      # Pydantic modely (DrugQuery, ResearchQuery, GuidelineQuery)
│   ├── src/api/               # FastAPI server (routes, cache, config, logging)
│   ├── tests/                 # unit_tests/ + integration_tests/
│   └── Makefile               # Development příkazy
├── specs/                     # Feature specifikace (SpecKit workflow)
│   ├── ROADMAP.md             # Master roadmap (12 features, 4 fáze)
│   └── NNN-feature-name/      # spec.md, plan.md, tasks.md
├── PRD-docs/                  # PRD dokumentace (strategie, architektura, UX)
└── .specify/                  # SpecKit framework + Constitution v1.1.1
```

## Feature Development Workflow (SpecKit)

```bash
cd langgraph-app
make speckit_new FEATURE="Description"   # Vytvoří branch + spec
# V Claude Code: /speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

## Constitution (5 Principů)

Definováno v `.specify/memory/constitution.md` v1.1.1:

1. **Graph-Centric Architecture** - Vše jako LangGraph nodes/edges, Send API
2. **Type Safety** - mypy --strict, typed dataclasses/TypedDict
3. **Test-First Development** - Testy PŘED implementací (TDD), regression testy
4. **Observability** - LangSmith tracing, structured logging, specific exceptions
5. **Modular Design** - Single responsibility per node, IMCPClient interface

Plus **Security Standards**: input validation, thread-safe IDs, async context managers, ReDoS-safe regex.

## Roadmap

### Phase 0: Foundation - DOKONČENO
- **001** LangGraph Foundation (State, Context, pytest fixtures)
- **002** MCP Infrastructure (SÚKL-mcp + BioMCP clients)

### Phase 1: Core Agents - PŘEVÁŽNĚ DOKONČENO
- **003** SÚKL Drug Agent (fuzzy search, 9 MCP tools)
- **004** VZP Pricing Agent - ČEKÁ NA IMPLEMENTACI
- **005** BioMCP PubMed Agent (interní CZ→EN překlad, citace)
- **006** Guidelines Agent (ČLS JEP PDFs, pgvector)

### Phase 2: Integration - DOKONČENO
- **007** Supervisor Orchestration (LLM intent classification — 8 typů, Send API)
- **009** Synthesizer Node (multi-agent response combination)

### Phase 3: UX & Deployment - DOKONČENO
- **011** FastAPI Backend (SSE streaming, Redis cache, rate limiting)
- **012** Next.js Frontend (chat interface, citace, OKLCH themes, mobile)

### Plánováno
- **004** VZP Pricing Agent
- **008** Cross-agent citation consolidation
- **010** Czech localization (medical abbreviations dictionary)

> **Dokončeno mimo roadmap:** Translation sandwich pattern odstraněn (commit 889b953) — PubMed agent nyní obsahuje interní CZ→EN překlad.

## Troubleshooting

**`ModuleNotFoundError: No module named 'agent'`** - Použijte `./dev.sh` nebo prefix `PYTHONPATH=src`.

**`uv run pytest` zamrzne na importu** - Těžký dependency graph spouští MCP client init. Použijte `.venv/bin/pytest` s `PYTHONPATH=src` prefixem.

**Translation testy selhávají/přeskočeny** - 5 testů vyžaduje `ANTHROPIC_API_KEY` nebo `OPENAI_API_KEY` v `.env`. Očekávané přeskočení v lokálním vývoji.

**Testy prosakují na reálné MCP servery** - Vždy `patch("agent.graph.get_mcp_clients")` v testech. Viz `tests/conftest.py`.

**Frontend se nepřipojí k backendu** - Ověřte, že FastAPI běží na :8000 a `NEXT_PUBLIC_API_URL=http://localhost:8000` je v `frontend/.env.local`.

**Playwright testy selhávají na mock routes** - Mock routes musí odpovídat `/api/v1/consult` (s version prefixem), ne `/api/consult`.

## Dokumentace

- **[QUICKSTART.md](./QUICKSTART.md)** - Rychlý start guide
- **[CLAUDE.md](./CLAUDE.md)** - Guide pro Claude Code
- **[MCP_INTEGRATION.md](./MCP_INTEGRATION.md)** - MCP integrace
- **[.specify/README.md](./.specify/README.md)** - SpecKit framework
- **[.specify/memory/constitution.md](./.specify/memory/constitution.md)** - Constitution v1.1.1
- **[specs/ROADMAP.md](./specs/ROADMAP.md)** - Detailní roadmap

---

**Verze:** 0.0.1 | **Aktualizováno:** 2026-02-15
