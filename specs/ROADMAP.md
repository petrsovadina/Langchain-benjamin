# Czech MedAI (Benjamin) - Feature Roadmap

**Project**: LangGraph-based AI Assistant for Czech Physicians
**Constitution**: v1.3.1
**Generated**: 2026-01-13
**Last Updated**: 2026-03-15

---

## Feature Decomposition Strategy

Projekt je rozložen na **12+ featur** organizovaných do **4 fází** podle závislostí a priorit. Průběžně přibývají cross-cutting features (audit, migrace).

### Strategie rozkladu:
1. **Phase 0: Foundation** - Infrastruktura a základní LangGraph setup
2. **Phase 1: Core Agents** - Implementace 4 specializovaných agentů
3. **Phase 2: Integration** - Supervisor orchestrace a citační systém
4. **Phase 3: UX & Deployment** - Frontend a production readiness
5. **Cross-cutting** - Audit, migrace, refaktoring (probíhají průběžně)

---

## Phase 0: Foundation

### 001-langgraph-foundation — DONE
**Branch**: `001-langgraph-foundation` (merged)
**Status**: Implementováno

- State schema (`State` dataclass s `add_messages`, `add_documents` reducery)
- `Context` TypedDict s runtime konfigurací
- pytest fixtures v `tests/conftest.py`
- LangSmith tracing integrace
- Base graph v `src/agent/graph.py`

---

### 002-mcp-infrastructure — DONE
**Branch**: `002-mcp-infrastructure` (merged)
**Status**: Implementováno

- Hexagonální MCP architektura (`domain/ports.py` → `IMCPClient` interface)
- `adapters/sukl_client.py` (JSON-RPC 2.0) + `adapters/biomcp_client.py` (REST)
- Domain entities a exceptions
- Health check endpointy

---

## Phase 1: Core Agents

### 003-sukl-drug-agent — DONE
**Branch**: `003-sukl-drug-agent` (merged)
**Status**: Implementováno

- `drug_agent_node` v `src/agent/nodes/drug_agent.py`
- SÚKL MCP integrace (search, details, reimbursement, ATC, ingredient)
- Query klasifikace (6 intent typů)
- Fuzzy matching přes SÚKL server
- Unit testy + integration testy

---

### 004-vzp-pricing-agent — PLANNED
**Priority**: P1 (Should Have)
**Status**: Dosud neimplementováno

**Scope**:
- Build `agent_pricing` node
- Implement VZP LEK-13 parser
- Create tools: `get_pricing`, `find_alternatives`

**Dependencies**: 003 (shares SÚKL codes)

---

### 005-biomcp-pubmed-agent — DONE
**Branch**: `005-biomcp-pubmed-agent` (merged)
**Status**: Implementováno

- `pubmed_agent_node` v `src/agent/nodes/pubmed_agent.py`
- BioMCP REST integrace
- Sandwich Pattern překlad (CZ→EN→CZ) v `translation.py`
- Citation extraction (PMID/DOI)
- Research query klasifikace

---

### 006-guidelines-agent — DONE
**Branch**: merged via multiple PRs
**Status**: Implementováno

- `guidelines_agent_node` v `src/agent/nodes/guidelines_agent.py`
- `search_guidelines()` v `utils/guidelines_storage.py` (asyncpg + pgvector)
- Supabase PostgreSQL integrace
- Semantic search s embedding vektory

---

## Phase 2: Integration

### 007-supervisor-orchestration — DONE
**Status**: Implementováno (součást core development)

- `supervisor_node` v `src/agent/nodes/supervisor.py`
- LLM intent klasifikace (8 intent typů)
- Send API pro paralelní dispatch
- Keyword fallback routing (`fallback_to_keyword_routing()`)
- Priority: Drug > Research > Guidelines > General

---

### 008-citation-system — DONE
**Status**: Implementováno (součást synthesizer)

- `extract_citations_from_message()` + `renumber_citations()` v `synthesizer.py`
- Inline citace `[1][2][3]` s globálním přečíslováním
- Reference list generování
- Podpora PMID, SUKL, CLS JEP zdrojů

---

### 009-synthesizer-node — DONE
**Status**: Implementováno

- `synthesizer_node` v `src/agent/nodes/synthesizer.py`
- Multi-agent response agregace
- Citation renumbering přes paralelní agenty
- Czech terminology validace (DM2T, ICHS, T2DM warnings)
- QuickConsult (single agent) vs Compound (multi-agent) formátování
- Confidence scoring (placeholder — implementace pending)

---

## Phase 3: UX & Deployment

### 010-czech-localization — DONE
**Status**: Integrováno do všech agentů

- Czech UI strings a error messages
- Medical abbreviation validace v synthesizeru
- Translation prompts v `utils/translation_prompts.py`

---

### 011-fastapi-backend — DONE
**Status**: Implementováno

- FastAPI server v `src/api/`
- SSE streaming (`/api/v1/consult`)
- Health check (`/health`)
- Redis cache, rate limiting (10/min)
- CORS, security headers, request ID middleware
- Pydantic validace vstupu

---

### 012-nextjs-frontend — DONE
**Status**: Implementováno

- Next.js 14 (TypeScript, React 18, Tailwind v4, shadcn/ui)
- Chat interface se streaming responses
- `CitedResponse` + `CitationBadge` komponenty
- `useConsult` hook s SSE klientem
- Playwright E2E testy

---

## Cross-cutting Features

### 013-supabase-migration — DONE
**Branch**: `013-supabase-migration` (merged, PR #18-#20)
**Status**: Implementováno

- Migrace guidelines storage na Supabase PostgreSQL + pgvector
- asyncpg connection pooling
- `GuidelinesStorage` class s embedding search
- Dual persistence model (LangGraph checkpointing + asyncpg)

---

### 005-remove-translation-layer — DONE
**Status**: Specifikováno (specs existují)

- Analýza odstranění translation layer
- Spec + plan + tasks v `specs/005-remove-translation-layer/`

---

### 001-audit-remediation — DONE
**Branch**: `001-audit-remediation` (merged, PR #21)
**Status**: Implementováno (57/57 tasks)

**P0 Security**:
- Error detail sanitization v produkci
- CORS fail-fast validace
- LLM timeout 60s přes `get_llm()` cache
- user_id validace

**P1 Hardening**:
- Full SHA-256 cache keys
- Docker credentials → env vars
- Stub testy opraveny
- Nové testy: cache, CORS, error sanitization

**P2 Cleanup**:
- LLM instance pooling (`llm_cache.py`)
- Odstraněn double execution fallback
- Unified pyproject.toml + uv.lock
- Odstraněn dead `State.next` field
- Unified `RESEARCH_KEYWORDS`
- Opraven `source_filter` bug

---

## Feature Dependency Graph

```
Phase 0 (DONE):
  001-langgraph-foundation    ──┐
  002-mcp-infrastructure      ──┼──┐
                                │  │
Phase 1 (3/4 DONE):            │  │
  003-sukl-drug-agent       ────┤  │  DONE
  004-vzp-pricing-agent     ────┘  │  PLANNED
  005-biomcp-pubmed-agent   ───────┤  DONE
  006-guidelines-agent      ───────┘  DONE
                                │
Phase 2 (DONE):                 │
  007-supervisor-orchestration ──┤
  008-citation-system          ──┤
  009-synthesizer-node         ──┘
                                │
Phase 3 (DONE):                 │
  010-czech-localization       ──┤
  011-fastapi-backend          ──┤
  012-nextjs-frontend          ──┘

Cross-cutting (DONE):
  013-supabase-migration
  001-audit-remediation (57 tasks)
```

---

## MVP Status

**11/12 originálních featur implementováno.**

| Feature | Status |
|---------|--------|
| 001-langgraph-foundation | DONE |
| 002-mcp-infrastructure | DONE |
| 003-sukl-drug-agent | DONE |
| 004-vzp-pricing-agent | PLANNED |
| 005-biomcp-pubmed-agent | DONE |
| 006-guidelines-agent | DONE |
| 007-supervisor-orchestration | DONE |
| 008-citation-system | DONE |
| 009-synthesizer-node | DONE |
| 010-czech-localization | DONE |
| 011-fastapi-backend | DONE |
| 012-nextjs-frontend | DONE |
| 013-supabase-migration | DONE |
| 001-audit-remediation | DONE |

---

## Remaining Work (Priority Order)

### P0 — Blokující pro produkci
1. **API key autentizace** — Constitution manduje auth na `/api/v1/consult`
2. **BioMCP deployment** — PubMed agent nefunkční bez remote BioMCP serveru

### P1 — Vysoká priorita
3. **004-vzp-pricing-agent** — Jediný neimplementovaný core agent
4. **Frontend CSP/Permissions-Policy** headers
5. **Confidence scoring** implementace (aktuálně placeholder 0.0)

### P2 — Střední priorita
6. **Next.js 14 → 15** upgrade
7. **GDPR dokumentace** LangSmith tracingu
8. **Agent-layer Settings** centralizace (constitution manduje)

### P3 — Nice to have
9. **paper-search-mcp** deployment pro rozšířený výzkum
10. **Migrace MCP klientů** na oficiální Python SDK

---

## SpecKit Workflow

Pro každou novou feature:
```bash
/speckit.specify [popis feature]
/speckit.clarify
/speckit.plan
/speckit.tasks
/speckit.analyze
/speckit.implement
```

---

## Related Documents

- [Constitution v1.3.1](../.specify/memory/constitution.md)
- [CLAUDE.md](../CLAUDE.md) — Development guidelines
- [SpecKit README](../.specify/README.md) — Framework documentation

---

**Status**: 11/12 core features done, audit complete, production readiness in progress
**Next Action**: Implement API key authentication or 004-vzp-pricing-agent
