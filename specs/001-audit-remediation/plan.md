# Implementation Plan: Audit Remediation

**Branch**: `001-audit-remediation` | **Date**: 2026-03-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-audit-remediation/spec.md`

## Summary

Remediate 20 findings from comprehensive expert audit of Czech MedAI. Fixes span 3 priority levels: P1 security (error sanitization, CORS validation, LLM timeouts), P2 hardening (cache keys, user_id validation, Docker credentials, test cleanup), and P3 cleanup (LLM reuse, dead code, dependencies). Delivered as 3 incremental PRs, one per priority level.

## Technical Context

**Language/Version**: Python >=3.10 (per constitution)
**Primary Framework**: LangGraph >=1.0.0 (per constitution)
**Additional Dependencies**: langchain-anthropic, fastapi, redis, asyncpg, pydantic-settings (all existing)
**Storage**: LangGraph checkpointing for graph state; asyncpg to Supabase PostgreSQL for application data (per constitution dual persistence model)
**Testing**: pytest with asyncio_mode="auto" (per constitution)
**Target Platform**: LangGraph Server via `langgraph dev` + FastAPI via uvicorn
**Project Type**: LangGraph Agent (single graph in `src/agent/graph.py`) + FastAPI bridge layer
**Performance Goals**: No regression in existing <30s timeout; LLM timeout at 60s per-call
**Constraints**: Async-first (per constitution), minimal external deps, no new dependencies needed
**Scale/Scope**: Modifies 15+ existing files, adds 1 new test file, no new nodes/edges

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Graph-Centric Architecture
- [x] Feature does not add new nodes/edges — modifies existing node internals only
- [x] All nodes continue to follow async signature: `async def node_name(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- [x] State transitions unchanged — Send API routing preserved
- [x] Graph structure remains visualizable in LangGraph Studio (removing dead `next` field simplifies State)

### Principle II: Type Safety & Schema Validation
- [x] `State` dataclass updated: `next` field removed (dead code)
- [x] `Context` TypedDict unchanged
- [x] Pydantic validation strengthened: `user_id` validator added to ConsultRequest
- [x] `LLM_TIMEOUT` constant added to `constants.py` with type annotation

### Principle III: Test-First Development
- [x] Unit tests planned for cache layer (`tests/unit_tests/api/test_cache.py`)
- [x] Stub tests cleaned up or replaced with behavioral tests
- [x] Regression tests for user_id validation, error sanitization, CORS validation
- [x] Test-first workflow: write test for each fix → verify fail → implement → verify pass

### Principle IV: Observability & Debugging
- [x] Error logging enhanced: `logger.error(..., exc_info=True)` on all error paths
- [x] Error response sanitization preserves server-side detail logging
- [x] No changes to LangSmith tracing configuration

### Principle V: Modular & Extensible Design
- [x] `LLM_TIMEOUT` extracted to `constants.py` (single source of truth)
- [x] `RESEARCH_KEYWORDS` consolidated from 2 locations to 1
- [x] Configuration uses `Settings` class, not hardcoded values

## Project Structure

### Documentation (this feature)

```text
specs/001-audit-remediation/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Research findings
├── data-model.md        # Phase 1: Entity changes
├── quickstart.md        # Phase 1: Implementation guide
├── contracts/
│   └── api-changes.md   # Phase 1: API behavior changes
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code Changes (by PR)

```text
# PR 1 (P1 — Security)
langgraph-app/src/api/routes.py         # Error sanitization (SSE + health)
langgraph-app/src/api/main.py           # CORS validation
langgraph-app/src/api/config.py         # CORS startup validator
langgraph-app/src/agent/constants.py    # Add LLM_TIMEOUT = 60
langgraph-app/src/agent/nodes/supervisor.py    # timeout=60
langgraph-app/src/agent/nodes/synthesizer.py   # timeout=60
langgraph-app/src/agent/nodes/general_agent.py # timeout=60
langgraph-app/src/agent/nodes/pubmed_agent.py  # timeout=60
langgraph-app/src/agent/nodes/translation.py   # timeout=60 (2 instances)

# PR 2 (P2 — Hardening)
langgraph-app/src/api/cache.py          # Full SHA-256, SCAN invalidation
langgraph-app/src/api/schemas.py        # user_id validator, version bump
langgraph-app/docker-compose.yml        # Externalize credentials, Redis auth
langgraph-app/tests/unit_tests/test_configuration.py  # Fix or remove
langgraph-app/tests/unit_tests/test_graph.py           # Fix or remove
langgraph-app/tests/unit_tests/test_graph_foundation.py # Fix or remove
langgraph-app/tests/integration_tests/test_api_server.py # Mock LLM/MCP
langgraph-app/tests/unit_tests/api/test_cache.py        # NEW: cache tests

# PR 3 (P3 — Cleanup)
langgraph-app/src/agent/graph.py        # Remove State.next, keep RESEARCH_KEYWORDS canonical
langgraph-app/src/agent/nodes/drug_agent.py       # Remove "next": "__end__"
langgraph-app/src/agent/nodes/pubmed_agent.py     # Remove "next", import RESEARCH_KEYWORDS
langgraph-app/src/agent/nodes/guidelines_agent.py # Remove "next"
langgraph-app/src/agent/nodes/synthesizer.py      # Remove "next"
langgraph-app/src/agent/nodes/general_agent.py    # Remove "next"
langgraph-app/src/api/routes.py         # Remove double execution fallback
langgraph-app/src/api/main.py           # Version bump 0.2.0
langgraph-app/src/api/routes.py         # Version bump 0.2.0 in health response
langgraph-app/src/api/schemas.py        # Version bump 0.2.0 in schema defaults
langgraph-app/pyproject.toml            # Version 0.2.0, cleanup deps, metadata
langgraph-app/uv.lock                   # NEW: generated via uv lock
```

**Structure Decision**: Existing project structure preserved. No new directories or modules needed. Changes are surgical edits to existing files plus 1 new test file and uv.lock.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | All changes align with constitution principles | N/A |
