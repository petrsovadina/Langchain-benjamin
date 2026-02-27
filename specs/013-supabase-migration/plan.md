# Implementation Plan: Supabase Migration (Replace InsForge)

**Branch**: `013-supabase-migration` | **Date**: 2026-02-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-supabase-migration/spec.md`

## Summary

Replace InsForge backend-as-a-service with direct Supabase PostgreSQL connectivity. The migration adapts `guidelines_storage.py` column mappings to match the existing Supabase `guidelines` table schema (UUID PKs, `external_id`, `full_content`, `source_type` enum, HNSW vector index), removes all InsForge configuration/documentation, and updates environment setup for Supabase credentials. No changes to Python domain models, LangGraph nodes, or agent logic — only the storage layer SQL and configuration files.

## Technical Context

**Language/Version**: Python ≥3.10 (per constitution)
**Primary Framework**: LangGraph ≥1.0.0 (per constitution)
**Additional Dependencies**: asyncpg (already installed), pgvector extension on Supabase
**Storage**: Direct asyncpg to Supabase PostgreSQL (pgvector for embeddings) — Note: this is NOT LangGraph checkpointing; guidelines storage is a separate concern outside the graph state
**Testing**: pytest with asyncio_mode="auto"
**Target Platform**: LangGraph Server via `langgraph dev`
**Project Type**: LangGraph Agent — storage utility refactoring (no graph changes)
**Performance Goals**: <2s vector similarity search (SC-005), <5s connection pool establishment (SC-006)
**Constraints**: Async-first, SSL mandatory for Supabase, service_role key for writes
**Scale/Scope**: 1 Python module (673 lines), 1 test file (~763 lines), 3 config files, 2 doc files, 1 file deletion

## Constitution Check

*GATE: Passed (pre-Phase 0). Re-checked after Phase 1 design.*

### Principle I: Graph-Centric Architecture
- [x] Feature designed as LangGraph nodes/edges in `src/agent/graph.py` — N/A: no graph changes, storage utility only
- [x] All nodes follow async signature — N/A: no new nodes
- [x] State transitions explicit — N/A: no state changes
- [x] Graph structure visualizable in LangGraph Studio — N/A: unchanged

### Principle II: Type Safety & Schema Validation
- [x] `State` dataclass updated with new fields — N/A: no new State fields
- [x] `Context` TypedDict updated with runtime params — N/A: no new Context params
- [x] All node inputs/outputs typed correctly — Storage functions maintain typed signatures (str UUID return)
- [x] Pydantic models for external data validation — GuidelineSection model unchanged, validation in storage layer

### Principle III: Test-First Development
- [x] Unit tests planned for each node in `tests/unit_tests/` — Update `test_guidelines_storage.py` (column names, UUID types)
- [x] Integration tests planned in `tests/integration_tests/` — Update `test_guidelines_storage_integration.py` (UUID assertions)
- [x] Test-first workflow confirmed — Update tests BEFORE modifying `guidelines_storage.py`

### Principle IV: Observability & Debugging
- [x] LangSmith tracing enabled — Already configured, unchanged
- [x] Logging added at node boundaries — Existing logger.debug/info calls retained
- [x] State transitions logged — N/A: no state transitions
- [x] Testing plan includes LangGraph Studio verification — Not needed (no graph changes)

### Principle V: Modular & Extensible Design
- [x] Nodes are small and single-responsibility — N/A: no new nodes
- [x] Reusable logic extracted to helper functions — Add `SOURCE_TO_ORG`/`ORG_TO_SOURCE` mapping dicts
- [x] Configuration parameters use Context, not hardcoded — DatabaseConfig.from_env() unchanged
- [x] Subgraphs used for complex multi-step operations — N/A

### Post-Phase 1 Re-check
- [x] No new constitution violations introduced
- [x] Direct asyncpg usage is existing pattern (not new ORM)
- [x] All type hints maintained (UUID str instead of int)

## Project Structure

### Documentation (this feature)

```text
specs/013-supabase-migration/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0: schema mapping decisions
├── data-model.md        # Phase 1: entity models & field mappings
├── quickstart.md        # Phase 1: setup & verification guide
├── contracts/
│   └── guidelines-storage-api.md  # Phase 1: SQL contracts per function
├── checklists/
│   └── requirements.md  # Quality checklist (passed)
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (files affected by migration)

```text
# Configuration (remove InsForge, add Supabase)
.mcp.json                                    # EDIT: remove insforge server entry
AGENTS.md                                    # DELETE: entire file (InsForge docs)
.claude/settings.local.json                  # EDIT: remove insforge permissions

# Environment
langgraph-app/.env                           # EDIT: add Supabase credentials
langgraph-app/.env.example                   # EDIT: uncomment Supabase, add DATABASE_URL

# Core storage module
langgraph-app/src/agent/utils/guidelines_storage.py  # MAJOR EDIT: column mapping, SQL, types

# Tests
langgraph-app/tests/unit_tests/utils/test_guidelines_storage.py         # MAJOR EDIT: mock data, assertions
langgraph-app/tests/integration_tests/test_guidelines_storage_integration.py  # EDIT: UUID types

# Documentation
CLAUDE.md                                    # EDIT: update DB config section
README.md                                    # EDIT: update setup instructions
```

```text
# Unchanged files (verified)
langgraph-app/src/agent/models/guideline_models.py       # Python model unchanged
langgraph-app/src/agent/nodes/guidelines_agent.py         # Calls storage, no SQL
langgraph-app/src/agent/graph.py                          # No DB references
langgraph-app/tests/unit_tests/nodes/test_guidelines_agent.py  # Mocks storage
langgraph-app/tests/integration_tests/test_guidelines_agent_flow.py  # Mocks storage
frontend/                                                 # No backend DB changes
```

**Structure Decision**: Default LangGraph project structure. This migration only touches the storage utility layer (`src/agent/utils/`) and configuration files. No new files created in `src/` — only modifications to existing files.

## Implementation Phases

### Phase A: Remove InsForge (P1 — User Story 2)

**Goal**: Zero InsForge references in codebase.

1. Remove `insforge` entry from `.mcp.json` (keep `supabase` entry)
2. Delete `AGENTS.md` file entirely
3. Remove InsForge-related permissions from `.claude/settings.local.json`
4. Remove `"insforge"` from `enabledMcpjsonServers` array

**Verification**: `grep -ri "insforge" --exclude-dir=specs --exclude-dir=.git . | wc -l` → 0

### Phase B: Environment Configuration (P2 — User Story 3)

**Goal**: Developer can connect to Supabase following documentation.

1. Update `langgraph-app/.env.example`:
   - Uncomment `SUPABASE_URL` and `SUPABASE_KEY`
   - Add `DATABASE_URL` template with Supabase format
   - Update `ENABLE_GUIDELINES_AGENT=true`
   - Remove "Future Features" label from database section
2. Update `langgraph-app/.env` (local only, not committed):
   - Set `DATABASE_URL` with real credentials
3. Update `CLAUDE.md`:
   - Replace `DATABASE_URL=postgresql://...` generic with Supabase-specific
   - Add `SUPABASE_URL` and `SUPABASE_KEY` to env vars section
4. Update `README.md`:
   - Update database setup section to reference Supabase

### Phase C: Storage Module Refactoring (P1 — User Story 1)

**Goal**: `guidelines_storage.py` works with Supabase schema.

**TDD Order**: Tests first, then implementation.

#### C.1: Update unit tests (`test_guidelines_storage.py`)
- Change mock column names in all SQL string assertions
- Change `id` mock values from int to UUID string
- Change `section_id` parameters from int to str
- Update `store_guideline` return type assertions (int → str)
- Add `SOURCE_TO_ORG` / `ORG_TO_SOURCE` mapping tests
- Update source filter tests to use enum cast (`::source_type`)

#### C.2: Update integration tests (`test_guidelines_storage_integration.py`)
- Change `record_id > 0` assertion to `isinstance(record_id, str)` + UUID format
- Update fixture `guideline_id` assertion for `external_id` lookup
- Verify `get_guideline_section` works with single `external_id` (no section_name needed)

#### C.3: Implement storage changes (`guidelines_storage.py`)

1. Add mapping constants:
   ```python
   SOURCE_TO_ORG: dict[GuidelineSource, str] = {
       GuidelineSource.CLS_JEP: "ČLS JEP",
       GuidelineSource.ESC: "ESC",
       GuidelineSource.ERS: "ERS",
   }
   ORG_TO_SOURCE: dict[str, GuidelineSource] = {v: k for k, v in SOURCE_TO_ORG.items()}
   ```

2. `store_guideline()`:
   - Change INSERT columns: `guideline_id`→`external_id`, `section_name`→`organization`, `content`→`full_content`, `source`→`source_type`, add `publication_year`
   - Change `ON CONFLICT (guideline_id, section_name)` → `ON CONFLICT (external_id)`
   - Map `source` to `"guidelines"` (enum) and derive `organization` from `SOURCE_TO_ORG`
   - Extract `publication_year` from `publication_date`
   - Extract `keywords`/`icd10_codes` from metadata
   - Change return type from `int` to `str`
   - Cast source_type: `$N::source_type`

3. `search_guidelines()`:
   - Change SELECT columns to match Supabase names
   - Change source filter: `AND source = $N` → `AND source_type = $N::source_type`
   - Map source filter value: `GuidelineSource.CLS_JEP` → `"guidelines"` (or keep as-is if filtering by specific source type)
   - Map returned columns back to backward-compatible Python dict keys
   - Handle `full_content IS NULL` → `""` empty string

4. `get_guideline_section()`:
   - Change lookup: `WHERE guideline_id = $1 AND section_name = $2` → `WHERE external_id = $1`
   - Change `section_id: int` → `section_id: str` (UUID)
   - Map returned columns to backward-compatible keys

5. `delete_guideline_section()`:
   - Change delete: `WHERE guideline_id = $1 AND section_name = $2` → `WHERE external_id = $1`
   - Change `section_id: int` → `section_id: str` (UUID)

### Phase D: Test Verification (P2 — User Story 4)

**Goal**: All 442+ tests pass.

1. Run unit tests: `PYTHONPATH=src uv run pytest tests/unit_tests/ -v`
2. Run integration tests: `PYTHONPATH=src uv run pytest tests/integration_tests/test_guidelines_storage_integration.py -v`
3. Run full suite: `PYTHONPATH=src uv run pytest tests/ -v`
4. Run linting: `PYTHONPATH=src uv run ruff check . && uv run ruff format --check .`
5. Run type checking: `PYTHONPATH=src uv run mypy --strict src/agent/utils/guidelines_storage.py`

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Supabase SSL connection failure | Low | High | `DatabaseConfig.from_env()` already handles SSL; test with quickstart |
| RLS blocks writes | Medium | High | Use service_role key, not anon key |
| Enum cast failure in SQL | Low | Medium | Test with `'guidelines'::source_type` in integration test |
| UUID type breaks downstream consumers | Low | High | Backward-compatible dict keys; only `id` type changes |
| Test mock data mismatches | Medium | Low | Update all mocks in Phase C.1 before implementation |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Direct asyncpg SQL (not ORM) | Constitution says "no direct ORM" but we use direct SQL | This IS the simple approach — asyncpg is already the pattern |
| `metadata` JSONB not used in Supabase | Supabase schema uses native columns instead of JSONB | Schema already exists with 26 tables; adapting Python is simpler than altering Supabase schema |

## Dependencies

```
Phase A (InsForge removal) ──────→ independent, can start immediately
Phase B (Environment config) ────→ independent, can start immediately
Phase C.1 (Update tests) ───────→ depends on research.md decisions (done)
Phase C.2 (Update integration) ──→ depends on C.1
Phase C.3 (Implement storage) ───→ depends on C.1 (TDD: tests first)
Phase D (Verification) ──────────→ depends on A + B + C
```

Phases A and B can run in parallel. Phase C follows TDD (tests before implementation).
