# Tasks: Supabase Migration (Replace InsForge)

**Input**: Design documents from `/specs/013-supabase-migration/`
**Prerequisites**: plan.md (loaded), spec.md (loaded), research.md, data-model.md, contracts/guidelines-storage-api.md, quickstart.md

**Tests**: Included — constitution Principle III mandates test-first development (TDD). Tests updated BEFORE implementation.

**Organization**: Tasks grouped by user story. US1 and US2 are both P1 (can run in parallel). US3 and US4 are P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Storage module**: `langgraph-app/src/agent/utils/guidelines_storage.py`
- **Unit tests**: `langgraph-app/tests/unit_tests/utils/test_guidelines_storage.py`
- **Integration tests**: `langgraph-app/tests/integration_tests/test_guidelines_storage_integration.py`
- **Config**: `.mcp.json`, `.claude/settings.local.json`, `AGENTS.md`
- **Env**: `langgraph-app/.env`, `langgraph-app/.env.example`
- **Docs**: `CLAUDE.md`, `README.md`
- All paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify prerequisites are in place before any implementation work

- [x] T001 Verify Supabase connection prerequisites: confirm `asyncpg` is in `langgraph-app/pyproject.toml` dependencies, confirm pgvector extension is available on Supabase project `higziqzcjmtmkzxbbzik`, confirm `guidelines` table exists with 24 columns and HNSW index `idx_guidelines_embedding`

**Checkpoint**: Prerequisites verified — implementation can begin

---

## Phase 2: User Story 2 — InsForge Configuration Removed (Priority: P1)

**Goal**: Zero InsForge references in the codebase (outside specs/ and .git/)

**Independent Test**: `grep -ri "insforge" --exclude-dir=specs --exclude-dir=.git . | wc -l` → 0

### Implementation for User Story 2

- [x] T002 [P] [US2] Remove `insforge` server entry (keys: `insforge.command`, `insforge.args`, `insforge.env`) from `.mcp.json` — keep only the `supabase` entry
- [x] T003 [P] [US2] Delete `AGENTS.md` file entirely (133 lines of InsForge SDK documentation with `alwaysApply: true` frontmatter)
- [x] T004 [P] [US2] Clean InsForge references from `.claude/settings.local.json`: remove 4 permission entries (`mcp__insforge__fetch-docs`, `mcp__insforge__get-backend-metadata`, `mcp__insforge__run-raw-sql`, `mcp__insforge__fetch-sdk-docs`) from `permissions.allow` array, and remove `"insforge"` from `enabledMcpjsonServers` array (keep `"supabase"`)
- [x] T005 [US2] Verify zero InsForge references: run `grep -ri "insforge" --exclude-dir=specs --exclude-dir=.git .` and confirm zero matches

**Checkpoint**: InsForge fully removed — no accidental connections possible

---

## Phase 3: User Story 1 — Backend Connects to Supabase (Priority: P1) MVP

**Goal**: `guidelines_storage.py` CRUD operations work with Supabase `guidelines` table schema (UUID PKs, `external_id`, `full_content`, `source_type` enum, HNSW index)

**Independent Test**: Run `PYTHONPATH=src uv run pytest tests/unit_tests/utils/test_guidelines_storage.py -v` — all tests pass with new column mappings

### Tests for User Story 1 (TDD — write first, verify they FAIL)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T006 [US1] Update `TestStoreGuideline` class in `langgraph-app/tests/unit_tests/utils/test_guidelines_storage.py`: change SQL assertion strings from `guideline_id`→`external_id`, `section_name`→`organization`, `content`→`full_content`, `source`→`source_type`; change `ON CONFLICT (guideline_id, section_name)`→`ON CONFLICT (external_id)`; change return type assertions from `int`→`str` (UUID); add `publication_year` parameter; add `keywords`/`icd10_codes` parameters; add test for `SOURCE_TO_ORG` mapping dict; add enum cast `::source_type` in SQL assertion
- [x] T007 [US1] Update `TestSearchGuidelines` class in `langgraph-app/tests/unit_tests/utils/test_guidelines_storage.py`: change SELECT column assertions from `guideline_id,title,section_name,content`→`external_id,title,organization,full_content`; change source filter assertion from `AND source = $N`→`AND source_type = $N::source_type`; update mock row data to use UUID `id` and new column names; verify backward-compatible Python dict keys (`guideline_id`, `section_name`, `content`, `source`); add test for `full_content IS NULL`→`""` empty string handling
- [x] T008 [US1] Update `TestGetGuidelineSection` and `TestDeleteGuidelineSection` classes in `langgraph-app/tests/unit_tests/utils/test_guidelines_storage.py`: change lookup SQL from `WHERE guideline_id = $1 AND section_name = $2`→`WHERE external_id = $1`; change `section_id` parameter type from `int`→`str` (UUID); change `WHERE id = $1`→`WHERE id = $1::uuid`; update mock row data with new column names; verify backward-compatible Python dict keys in return values
- [ ] T009 [US1] Update integration tests in `langgraph-app/tests/integration_tests/test_guidelines_storage_integration.py`: change `record_id > 0` assertion→`isinstance(record_id, str)` with UUID format check; update `get_guideline_section` call to use `guideline_id=` (maps to `external_id`) without requiring `section_name`; update expected dict keys in assertions

### Implementation for User Story 1

- [x] T010 [US1] Add `SOURCE_TO_ORG` and `ORG_TO_SOURCE` mapping constants in `langgraph-app/src/agent/utils/guidelines_storage.py` after the `EMBEDDING_DIMENSIONS` constant: `SOURCE_TO_ORG: dict[GuidelineSource, str]` mapping `CLS_JEP→"ČLS JEP"`, `ESC→"ESC"`, `ERS→"ERS"`; and reverse `ORG_TO_SOURCE: dict[str, GuidelineSource]`
- [x] T011 [US1] Refactor `store_guideline()` in `langgraph-app/src/agent/utils/guidelines_storage.py` per contract `contracts/guidelines-storage-api.md`: change INSERT columns (`external_id`, `title`, `organization`, `full_content`, `publication_year`, `publication_date`, `source_type`, `url`, `embedding`, `keywords`, `icd10_codes`); use `ON CONFLICT (external_id)`; derive `organization` from `SOURCE_TO_ORG[source]`; extract `publication_year` from date string; set `source_type` to `"guidelines"` with `::source_type` cast; extract `keywords`/`icd10_codes` from metadata; change return type `int`→`str`; change `record_id` extraction from `row["id"]` int→str(UUID)
- [x] T012 [US1] Refactor `search_guidelines()` in `langgraph-app/src/agent/utils/guidelines_storage.py` per contract: change SELECT columns to `id, external_id, title, organization, full_content, publication_date, source_type, url, keywords, icd10_codes`; change source filter to `AND source_type = $N::source_type`; map source_filter value to `"guidelines"` when `GuidelineSource` provided; map returned columns to backward-compatible dict keys (`"guideline_id"←external_id`, `"section_name"←organization`, `"content"←full_content or ""`, `"source"←source_type`); reconstruct `"metadata"` dict from `keywords`/`icd10_codes` columns; change `"id"` value from int→str(UUID)
- [x] T013 [US1] Refactor `get_guideline_section()` in `langgraph-app/src/agent/utils/guidelines_storage.py`: change lookup from `WHERE guideline_id = $1 AND section_name = $2`→`WHERE external_id = $1` (single unique key); change `section_id: int | None`→`section_id: str | None`; add `::uuid` cast for `WHERE id = $1::uuid`; update SELECT columns to match Supabase names; map returned columns to backward-compatible dict keys; handle `full_content IS NULL`→`""`
- [x] T014 [US1] Refactor `delete_guideline_section()` in `langgraph-app/src/agent/utils/guidelines_storage.py`: change delete from `WHERE guideline_id = $1 AND section_name = $2`→`WHERE external_id = $1`; change `section_id: int | None`→`section_id: str | None`; add `::uuid` cast for `WHERE id = $1::uuid`
- [ ] T015 [US1] Run unit tests to verify TDD cycle complete: `cd langgraph-app && PYTHONPATH=src uv run pytest tests/unit_tests/utils/test_guidelines_storage.py -v` — all tests must pass

**Checkpoint**: Storage module works with Supabase schema. Unit tests pass. Core MVP delivered.

---

## Phase 4: User Story 3 — Environment Configuration & Documentation (Priority: P2)

**Goal**: A new developer can set up Supabase connectivity following updated docs in under 5 minutes

**Independent Test**: A fresh clone with `.env.example` values filled in connects to Supabase and passes health check

### Implementation for User Story 3

- [ ] T016 [P] [US3] Update `langgraph-app/.env.example`: uncomment `SUPABASE_URL` and `SUPABASE_KEY` variables; add `DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres?sslmode=require` template; change `ENABLE_GUIDELINES_AGENT=false`→`true`; remove any "Future Features" labels from database section; add comment explaining `DATABASE_URL` takes precedence over `SUPABASE_URL`
- [ ] T017 [P] [US3] Update `CLAUDE.md` Environment Variables section: replace generic `DATABASE_URL=postgresql://...` with Supabase-specific connection string format; add `SUPABASE_URL` and `SUPABASE_KEY` descriptions; update the "Active Technologies" section to mention Supabase; ensure `.env` is listed in `langgraph-app/.gitignore` (safety check)
- [ ] T018 [P] [US3] Update `README.md` database setup section: replace any generic PostgreSQL / InsForge references with Supabase Cloud setup instructions; add link to Supabase dashboard; document both connection methods (DATABASE_URL vs SUPABASE_URL+KEY)
- [ ] T019 [US3] Configure `langgraph-app/.env` with real Supabase credentials (local only, NOT committed): set `DATABASE_URL=postgresql://postgres:zOr3gt60kbKourMJ@db.higziqzcjmtmkzxbbzik.supabase.co:5432/postgres?sslmode=require`; verify `.env` is in `.gitignore`

**Checkpoint**: Documentation complete — new developer can set up Supabase following docs

---

## Phase 5: User Story 4 — All Existing Tests Pass (Priority: P2)

**Goal**: Zero regressions — all 442+ backend tests pass, linting clean, types correct

**Independent Test**: `cd langgraph-app && PYTHONPATH=src uv run pytest tests/ -v` — all tests pass

### Verification for User Story 4

- [ ] T020 [US4] Run full unit test suite: `cd langgraph-app && PYTHONPATH=src uv run pytest tests/unit_tests/ -v` — verify all 442+ tests pass (no regressions in non-guidelines tests)
- [ ] T021 [US4] Run integration tests against live Supabase: `cd langgraph-app && PYTHONPATH=src uv run pytest tests/integration_tests/test_guidelines_storage_integration.py -v` — verify store/search/get/delete operations work with real Supabase
- [ ] T022 [US4] Run linting and formatting: `cd langgraph-app && PYTHONPATH=src uv run ruff check . && uv run ruff format --check .` — zero warnings/errors
- [ ] T023 [US4] Run type checking: `cd langgraph-app && PYTHONPATH=src uv run mypy --strict src/agent/utils/guidelines_storage.py` — zero errors with --strict mode

**Checkpoint**: Full quality gates pass — ready for merge

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T024 [P] Run quickstart.md smoke test from `specs/013-supabase-migration/quickstart.md` section 5: store → retrieve → search → delete cycle against live Supabase
- [ ] T025 Final InsForge audit: `grep -ri "insforge" --include="*.py" --include="*.json" --include="*.md" --exclude-dir=specs --exclude-dir=.git .` — zero matches; verify `.mcp.json` has only `supabase` entry; verify `AGENTS.md` does not exist

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify prerequisites immediately
- **US2 - InsForge Removal (Phase 2)**: No dependencies — can start after Setup (or in parallel)
- **US1 - Storage TDD (Phase 3)**: No dependencies on US2 — can start after Setup (or in parallel with US2)
- **US3 - Environment & Docs (Phase 4)**: Depends on Phase 2 (InsForge removed) and Phase 3 (storage code finalized)
- **US4 - Test Verification (Phase 5)**: Depends on ALL previous phases (A+B+C complete)
- **Polish (Phase 6)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: Independent — can start immediately after Setup
- **US2 (P1)**: Independent — can start immediately after Setup, parallel with US1
- **US3 (P2)**: Depends on US1 + US2 (needs finalized code and removed InsForge for accurate docs)
- **US4 (P2)**: Depends on US1 + US2 + US3 (full suite validation)

### Within User Story 1 (TDD Order)

1. T006–T009: Update tests FIRST (must FAIL before implementation)
2. T010: Add mapping constants (enables other implementation tasks)
3. T011: Refactor store_guideline() → run tests for store
4. T012: Refactor search_guidelines() → run tests for search
5. T013–T014: Refactor get/delete → run tests for get/delete
6. T015: Full unit test verification

### Parallel Opportunities

**Phase 2 (US2)**: T002, T003, T004 all touch different files → run in parallel
**Phase 3 (US1) tests**: T006, T007, T008 modify different test classes in same file → sequential but independent
**Phase 3 (US1) implementation**: T011–T014 modify same file → strictly sequential
**Phase 4 (US3)**: T016, T017, T018 touch different files → run in parallel
**Cross-story**: US1 and US2 are independent P1 stories → can run in parallel

---

## Parallel Example: User Story 2

```bash
# All three InsForge removal tasks touch different files — launch in parallel:
Task: "T002 [P] [US2] Remove insforge entry from .mcp.json"
Task: "T003 [P] [US2] Delete AGENTS.md"
Task: "T004 [P] [US2] Clean insforge from .claude/settings.local.json"
# Then sequential verification:
Task: "T005 [US2] Verify zero InsForge references"
```

## Parallel Example: Cross-Story P1

```bash
# US1 and US2 are independent P1 stories — launch in parallel:
Story US2: T002→T003→T004→T005 (InsForge removal)
Story US1: T006→T007→T008→T009→T010→T011→T012→T013→T014→T015 (Storage TDD)
# Both can proceed simultaneously, no shared files
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2)

1. Complete Phase 1: Setup (verify prerequisites)
2. Complete Phase 2: US2 (InsForge removal) — parallel with US1
3. Complete Phase 3: US1 (storage TDD) — core MVP
4. **STOP and VALIDATE**: Unit tests pass for storage module
5. The system can now connect to Supabase and perform CRUD on guidelines

### Incremental Delivery

1. Setup → Foundation ready
2. US2 (InsForge removal) → Clean codebase, no confusion
3. US1 (Storage TDD) → Core functionality works → **MVP!**
4. US3 (Environment & Docs) → Developer onboarding ready
5. US4 (Test Verification) → Full quality gates pass → **Merge ready!**

### Single Developer Strategy (Recommended)

Since this migration involves 1 Python module + config files:
1. Phase 2 (US2) first — quick wins, 4 tasks, ~10 minutes
2. Phase 3 (US1) — core TDD work, 10 tasks, ~60 minutes
3. Phase 4 (US3) — docs update, 4 tasks, ~15 minutes
4. Phase 5 (US4) — run all checks, 4 tasks, ~10 minutes
5. Phase 6 — final validation, 2 tasks, ~5 minutes

---

## Notes

- [P] tasks = different files, no dependencies
- [US1–US4] labels map tasks to spec.md user stories for traceability
- TDD is NON-NEGOTIABLE per constitution Principle III — tests updated before implementation
- All storage function signatures use backward-compatible dict keys to avoid breaking downstream consumers
- `section_id: int` → `str` (UUID) is a breaking change for callers — verify no other code passes int IDs
- `guidelines_storage.py` is the ONLY source file modified — no changes to graph, nodes, or models
- Commit after each user story completion (not individual tasks)
