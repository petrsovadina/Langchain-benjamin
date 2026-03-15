# Tasks: Audit Remediation

**Input**: Design documents from `/specs/001-audit-remediation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Constitution mandates test-first (Principle III). New tests are included for cache layer (US8), test cleanup (US7), and regression tests for security fixes.

**Organization**: Tasks grouped by user story priority. US1–US3 = PR 1 (P1), US4–US8 = PR 2 (P2), US9–US12 = PR 3 (P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **LangGraph project**: `langgraph-app/src/agent/`, `langgraph-app/tests/`
- **API layer**: `langgraph-app/src/api/`
- **Tests**: `langgraph-app/tests/unit_tests/` for nodes, `langgraph-app/tests/integration_tests/` for graphs
- All paths relative to repository root

---

## Phase 1: Setup

**Purpose**: Add shared constants and verify baseline test suite passes

- [x] T001 Add `LLM_TIMEOUT = 60` constant to `langgraph-app/src/agent/constants.py`
- [x] T002 Run full test suite baseline: `PYTHONPATH=src uv run pytest tests/ -v` and record pass count (449 passed)

**Checkpoint**: Baseline established, constants available for all phases

---

## Phase 2: Foundational (No blockers for this feature)

**Purpose**: No foundational changes needed — all user stories modify existing files independently.

**Checkpoint**: Proceed directly to user story phases.

---

## Phase 3: US1 — Error Response Sanitization (Priority: P1)

**Goal**: Prevent internal error details from leaking to clients in production mode.

**Independent Test**: Trigger errors and verify SSE events contain generic messages when `environment=production`.

### Test First (Constitution Principle III)

- [x] T003 [US1] Write regression test: SSE error sanitization in `langgraph-app/tests/unit_tests/api/test_error_sanitization.py` — test that error events contain generic message in production mode and raw message in development mode. Verify test FAILS before implementation.

### Implementation

- [x] T004 [US1] Sanitize SSE catch-all error in `langgraph-app/src/api/routes.py:313-322` — replace `"detail": str(e)` with conditional: use `"An unexpected error occurred"` when `settings.environment == "production"`, keep `str(e)` otherwise. Import `settings` from `api.config`. Add `logger.error(str(e), exc_info=True)` before sanitized response.
- [x] T005 [P] [US1] Sanitize health endpoint SUKL error in `langgraph-app/src/api/routes.py:72` — replace `f"error: {str(e)}"` with `"error"` when `settings.environment == "production"`. Log full error server-side.
- [x] T006 [P] [US1] Sanitize health endpoint BioMCP error in `langgraph-app/src/api/routes.py:88` — same pattern as T005
- [x] T007 [P] [US1] Sanitize health endpoint DB errors in `langgraph-app/src/api/routes.py:100,104` — replace `f"error: {str(e)}"` with `"error"` when `settings.environment == "production"`. Log full error server-side.
- [x] T007b [US1] Verify regression test T003 now PASSES after implementation (6/6 passed)

**Checkpoint**: `grep -rn 'str(e)' src/api/routes.py` should show zero matches in error handler blocks

---

## Phase 4: US2 — CORS Production Safety (Priority: P1)

**Goal**: API fails fast on startup when CORS misconfigured for production.

**Independent Test**: Instantiate `Settings(environment="production", cors_origins=[])` and verify `ValidationError` raised.

### Test First (Constitution Principle III)

- [x] T008 [US2] Write regression test: CORS validation in `langgraph-app/tests/unit_tests/api/test_cors_validation.py` — test production fails with empty origins, development allows wildcard. Verify test FAILS before implementation.

### Implementation

- [x] T009 [US2] Add CORS startup validator to `langgraph-app/src/api/config.py` — add `@model_validator(mode="after")` that raises `ValueError` when `environment == "production"` and `cors_origins` is empty or contains `"*"`
- [x] T010 [US2] Fix CORS middleware in `langgraph-app/src/api/main.py:131` — remove `["*"]` fallback: change `settings.cors_origins if settings.cors_origins else ["*"]` to `settings.cors_origins`
- [x] T010b [US2] Verify regression test T008 now PASSES after implementation (6/6 passed)

**Checkpoint**: Starting API with `ENVIRONMENT=production CORS_ORIGINS=` should fail immediately

---

## Phase 5: US3 — LLM Timeout Protection (Priority: P1)

**Goal**: All ChatAnthropic instances have explicit timeout=60.

**Independent Test**: `grep -rn "timeout=None" src/agent/nodes/` returns zero results.

### Implementation

- [x] T011 [P] [US3] Fix timeout in `langgraph-app/src/agent/nodes/supervisor.py:129` — replace `timeout=None` with `timeout=LLM_TIMEOUT`, import from `agent.constants`
- [x] T012 [P] [US3] Fix timeout in `langgraph-app/src/agent/nodes/synthesizer.py:607` — replace `timeout=None` with `timeout=LLM_TIMEOUT`, import from `agent.constants`
- [x] T013 [P] [US3] Fix timeout in `langgraph-app/src/agent/nodes/general_agent.py:65` — replace `timeout=None` with `timeout=LLM_TIMEOUT`, import from `agent.constants`
- [x] T014 [P] [US3] Fix timeout in `langgraph-app/src/agent/nodes/pubmed_agent.py:381` — replace `timeout=None` with `timeout=LLM_TIMEOUT`, import from `agent.constants`
- [x] T015 [P] [US3] Fix timeout in `langgraph-app/src/agent/nodes/translation.py:73` — replace `timeout=None` with `timeout=LLM_TIMEOUT`, import from `agent.constants`
- [x] T016 [P] [US3] Fix timeout in `langgraph-app/src/agent/nodes/translation.py:145` — replace `timeout=None` with `timeout=LLM_TIMEOUT`, import from `agent.constants`
- [x] T017 [P] [US3] Cleanup: remove redundant `stop=None` from ChatAnthropic calls (supervisor:130, translation:73,145, pubmed_agent:381) — `stop=None` is the default, removing reduces noise

**Checkpoint**: `grep -rn "timeout=None" src/agent/` returns zero results. Run full test suite.

---

**PR 1 CHECKPOINT**: US1+US2+US3 complete. Run `PYTHONPATH=src uv run pytest tests/ -v`. All tests pass. Create PR 1.

---

## Phase 6: US4 — Cache Key Collision Prevention (Priority: P2)

**Goal**: Cache keys use full SHA-256 hash (64 hex chars).

**Independent Test**: Call `generate_cache_key("test", "quick")` and verify key contains 64-char hash segment.

### Implementation

- [x] T018 [US4] Fix cache key in `langgraph-app/src/api/cache.py:66` — remove `[:16]` truncation from `hashlib.sha256(query.encode()).hexdigest()[:16]`
- [x] T019 [US4] Fix cache invalidation in `langgraph-app/src/api/cache.py:143` — replace `client.keys(pattern)` with `client.scan_iter(match=pattern, count=100)` async iteration

**Checkpoint**: `generate_cache_key("test", "quick")` returns key with 64-char hash

---

## Phase 7: US5 — User ID Input Validation (Priority: P2)

**Goal**: user_id validated for format, length, and control characters.

**Independent Test**: POST `/api/v1/consult` with `user_id: "ab\ncd"` returns 400.

### Implementation

- [x] T020 [US5] Add user_id field_validator to `langgraph-app/src/api/schemas.py:33` — add `@field_validator("user_id")` that validates regex `^[a-zA-Z0-9_-]{1,64}$` when value is not None, rejecting control characters and overlength

**Checkpoint**: Invalid user_id values rejected with 400 status

---

## Phase 8: US6 — Docker Credentials Externalization (Priority: P2)

**Goal**: No hardcoded credentials in docker-compose.yml.

**Independent Test**: `grep -n "postgres:postgres" docker-compose.yml` returns zero results.

### Implementation

- [x] T021 [US6] Remove hardcoded DATABASE_URL from `langgraph-app/docker-compose.yml:15` — remove the inline `DATABASE_URL=postgresql://postgres:postgres@...` line (env_file already provides it)
- [x] T022 [P] [US6] Replace hardcoded Postgres credentials in `langgraph-app/docker-compose.yml:48-49` — change `POSTGRES_USER=postgres` to `POSTGRES_USER=${POSTGRES_USER:-postgres}` and `POSTGRES_PASSWORD=postgres` to `POSTGRES_PASSWORD=${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}`
- [x] T023 [P] [US6] Add Redis auth to `langgraph-app/docker-compose.yml:34` — add `--requirepass ${REDIS_PASSWORD:-changeme}` to redis-server command
- [x] T024 [US6] Bind ports to localhost in `langgraph-app/docker-compose.yml` — change `"6379:6379"` to `"127.0.0.1:6379:6379"` and `"5432:5432"` to `"127.0.0.1:5432:5432"`
- [x] T025 [P] [US6] Create `langgraph-app/.env.docker.example` with placeholder credentials template

**Checkpoint**: `grep -n "postgres:postgres" docker-compose.yml` returns zero results

---

## Phase 9: US7 — Broken Test Cleanup (Priority: P2)

**Goal**: Remove or replace all stub/placeholder tests.

**Independent Test**: `grep -rn "changeme\|isinstance(graph, Pregel)" tests/` returns zero results.

### Implementation

- [x] T026 [P] [US7] Fix or remove `langgraph-app/tests/unit_tests/test_configuration.py` — replace `isinstance(graph, Pregel)` placeholder with behavioral test (e.g., test graph has expected nodes) or delete file
- [x] T027 [P] [US7] Fix or remove `langgraph-app/tests/unit_tests/test_graph.py` (already removed) — replace `{"changeme": "some_val"}` stub with valid State-based test or delete file
- [x] T028 [P] [US7] Fix or remove `langgraph-app/tests/unit_tests/test_graph_foundation.py` (already removed) — update obsolete `"Echo:"` behavior assertions to match current graph behavior or delete file
- [x] T029 [US7] Fix `langgraph-app/tests/integration_tests/test_api_server.py` — mocked graph, fixed SSE decode consult tests — add proper LLM/MCP mocks (`patch("agent.graph.get_mcp_clients")`) so tests don't require live services

**Checkpoint**: All tests pass, zero stub tests remain

---

## Phase 10: US8 — Cache Layer Test Coverage (Priority: P2)

**Goal**: Unit tests for Redis cache layer with mocked Redis client.

**Independent Test**: Run `PYTHONPATH=src uv run pytest tests/unit_tests/api/test_cache.py -v` — all pass.

### Implementation

- [x] T030 [US8] Create `langgraph-app/tests/unit_tests/api/test_cache.py` — 11 tests covering key gen, miss/hit, graceful degradation, scan_iter with 4+ test scenarios:
  - `test_cache_miss_returns_none` — mock Redis client returns None
  - `test_cache_hit_returns_data` — mock Redis client returns JSON
  - `test_cache_expiry_returns_none` — mock expired key
  - `test_redis_unavailable_graceful_degradation` — mock RedisError, verify None returned
  - `test_generate_cache_key_full_sha256` — verify key length is 64 hex chars (post-T018 fix)
  - `test_invalidate_uses_scan` — verify `scan_iter` called instead of `keys`

**Checkpoint**: Cache tests pass. Run full suite: `PYTHONPATH=src uv run pytest tests/ -v`

---

**PR 2 CHECKPOINT**: US4+US5+US6+US7+US8 complete. All tests pass. Create PR 2.

---

## Phase 11: US9 — LLM Instance Reuse (Priority: P3)

**Goal**: ChatAnthropic instances reused when model parameters are identical.

**Independent Test**: Verify supervisor and synthesizer share LLM instance across invocations with same params.

### Implementation

- [x] T031 [US9] Create LLM instance cache utility in `langgraph-app/src/agent/utils/llm_cache.py` — module-level dict keyed by `(model_name, temperature, timeout)`, function `get_llm(model_name, temperature, timeout) -> ChatAnthropic` that returns cached or creates new
- [x] T0\1 [US9] Update `langgraph-app/src/agent/nodes/supervisor.py` IntentClassifier — replace inline `ChatAnthropic(...)` with `get_llm()` call
- [x] T0\1 [P] [US9] Update `langgraph-app/src/agent/nodes/synthesizer.py` — replace inline ChatAnthropic with `get_llm()` call
- [x] T0\1 [P] [US9] Update `langgraph-app/src/agent/nodes/general_agent.py` — replace inline ChatAnthropic with `get_llm()` call
- [x] T0\1 [P] [US9] Update `langgraph-app/src/agent/nodes/pubmed_agent.py` — replace inline ChatAnthropic with `get_llm()` call
- [x] T0\1 [P] [US9] Update `langgraph-app/src/agent/nodes/translation.py` (both functions) — replace inline ChatAnthropic with `get_llm()` call

**Checkpoint**: All nodes use `get_llm()`, tests pass

---

## Phase 12: US10 — Double Execution Elimination (Priority: P3)

**Goal**: SSE streaming captures final state from stream without ainvoke() fallback.

**Independent Test**: Verify routes.py has no `ainvoke()` fallback block.

### Implementation

- [x] T0\1 [US10] Rewrite state capture in `langgraph-app/src/api/routes.py:200-270` — capture final state from root `on_chain_end` event in `astream_events()` loop instead of only checking `event.name == "synthesizer"`. Remove the `ainvoke()` fallback block (lines 253-270).

**Checkpoint**: `grep -n "ainvoke" src/api/routes.py` returns zero results in consult_stream_generator

---

## Phase 13: US11 — Dead Code Removal (Priority: P3)

**Goal**: Remove State.next field, consolidate RESEARCH_KEYWORDS, fix source_filter.

**Independent Test**: `grep -rn '"next": "__end__"' src/agent/nodes/` returns zero results.

### Implementation

- [x] T0\1 [US11] Remove `next` field from State dataclass in `langgraph-app/src/agent/graph.py` — remove `next: Annotated[str, _keep_last] = "__end__"` and the `_keep_last` reducer function (if unused elsewhere)
- [x] T0\1 [P] [US11] Remove all `"next": "__end__"` from `langgraph-app/src/agent/nodes/drug_agent.py` return dicts (3 occurrences)
- [x] T0\1 [P] [US11] Remove all `"next": "__end__"` from `langgraph-app/src/agent/nodes/pubmed_agent.py` return dicts (5 occurrences)
- [x] T0\1 [P] [US11] Remove all `"next": "__end__"` from `langgraph-app/src/agent/nodes/guidelines_agent.py` return dicts (5 occurrences)
- [x] T0\1 [P] [US11] Remove all `"next": "__end__"` from `langgraph-app/src/agent/nodes/synthesizer.py` return dicts (3 occurrences)
- [x] T0\1 [P] [US11] Remove all `"next": "__end__"` from `langgraph-app/src/agent/nodes/general_agent.py` return dicts (2 occurrences)
- [x] T0\1 [US11] Consolidate RESEARCH_KEYWORDS — remove local definition from `langgraph-app/src/agent/nodes/pubmed_agent.py:60-77`, add `from agent.graph import RESEARCH_KEYWORDS` import
- [x] T0\1 [US11] Fix source_filter in `langgraph-app/src/agent/utils/guidelines_storage.py` — remove misleading `source_filter` parameter from public search function, hardcode `"guidelines"` internally

**Checkpoint**: Zero `"next": "__end__"` in nodes, one `RESEARCH_KEYWORDS` definition

---

## Phase 14: US12 — Dependency Cleanup (Priority: P3)

**Goal**: Clean deps, add uv.lock, unify version to 0.2.0.

**Independent Test**: `uv lock` succeeds, `grep 'version' pyproject.toml` shows `0.2.0`.

### Implementation

- [x] T0\1 [US12] Update `langgraph-app/pyproject.toml` version and metadata — set `version = "0.2.0"`, update `description` from template text to "Czech MedAI — AI asistent pro české lékaře", update `authors` from template to project author
- [x] T0\1 [US12] Remove `[project.optional-dependencies]` section from `langgraph-app/pyproject.toml:43-50` — dev deps already in `[dependency-groups]` with newer versions
- [x] T0\1 [US12] Remove `sse-starlette` from dependencies in `langgraph-app/pyproject.toml:34` — unused, code uses StreamingResponse directly
- [x] T0\1 [US12] Update version in `langgraph-app/src/api/main.py:99` from `"0.1.0"` to `"0.2.0"`
- [x] T0\1 [P] [US12] Update version in `langgraph-app/src/api/main.py:254` root endpoint from `"0.1.0"` to `"0.2.0"`
- [x] T0\1 [P] [US12] Update version in `langgraph-app/src/api/routes.py:112` health response from `"0.1.0"` to `"0.2.0"`
- [x] T0\1 [P] [US12] Update version default/example in `langgraph-app/src/api/schemas.py:258,260` from `"0.1.0"` to `"0.2.0"`
- [x] T0\1 [US12] Generate `langgraph-app/uv.lock` by running `cd langgraph-app && uv lock`

**Checkpoint**: Version consistent everywhere, uv.lock committed

---

**PR 3 CHECKPOINT**: US9+US10+US11+US12 complete. Full test suite passes. Create PR 3.

---

## Phase 15: Polish & Cross-Cutting Concerns

**Purpose**: Final validation across all PRs

- [x] T0\1 Run full test suite: `PYTHONPATH=src uv run pytest tests/ -v` — verify 449+ tests passing, zero stub tests
- [x] T0\1b Verify cache layer test coverage: `PYTHONPATH=src uv run pytest tests/unit_tests/api/test_cache.py -v --tb=short` — confirm ≥4 test scenarios pass (SC-006)
- [x] T0\1 Run lint + type check: `uv run ruff format . && uv run ruff check . && uv run mypy --strict src/agent/`
- [x] T0\1 Run quickstart.md validation commands (security checks section)
- [x] T0\1 Update CLAUDE.md if any conventions changed (e.g., new LLM_TIMEOUT constant, removed State.next, `get_llm()` utility)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Skipped — no blocking prerequisites
- **US1–US3 (Phases 3–5)**: Depend on Phase 1 (constants). Can run in parallel with each other.
- **US4–US8 (Phases 6–10)**: Independent of US1–US3 but shipped in PR 2 after PR 1 merges
- **US9–US12 (Phases 11–14)**: US9 depends on US3 (timeout constant). US11 is independent. US12 is independent.
- **Polish (Phase 15)**: After all PRs merged

### User Story Dependencies

- **US1 (Error sanitization)**: Independent
- **US2 (CORS safety)**: Independent
- **US3 (LLM timeout)**: Depends on T001 (LLM_TIMEOUT constant)
- **US4 (Cache key)**: Independent
- **US5 (user_id validation)**: Independent
- **US6 (Docker credentials)**: Independent
- **US7 (Test cleanup)**: Independent
- **US8 (Cache tests)**: Should run after US4 (cache key fix) for correct assertions
- **US9 (LLM reuse)**: Depends on US3 (timeout constant established)
- **US10 (Double execution)**: Independent
- **US11 (Dead code)**: Independent
- **US12 (Dependency cleanup)**: Independent

### Parallel Opportunities

**Within PR 1 (P1)**:
- T004, T005, T006 can run in parallel (different health endpoint error locations)
- T011–T016 can ALL run in parallel (different node files, same change pattern)

**Within PR 2 (P2)**:
- T022, T023 can run in parallel (different docker-compose sections)
- T026, T027, T028 can run in parallel (different test files)

**Within PR 3 (P3)**:
- T033, T034, T035, T036 can run in parallel (different node files for LLM reuse)
- T039, T040, T041, T042, T043 can ALL run in parallel (removing "next" from different files)
- T049, T050, T051, T052 can run in parallel (version bump in different files)

---

## Implementation Strategy

### PR 1 First (P1 Security — Blocks Deployment)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phases 3–5: US1+US2+US3 (T003–T017)
3. **VALIDATE**: Run full test suite, security grep checks
4. Create PR 1, merge to main

### PR 2 Second (P2 Hardening)

1. Complete Phases 6–10: US4+US5+US6+US7+US8 (T018–T030)
2. **VALIDATE**: Run full test suite, no stub tests, cache tests pass
3. Create PR 2, merge to main

### PR 3 Third (P3 Cleanup)

1. Complete Phases 11–14: US9+US10+US11+US12 (T031–T053)
2. **VALIDATE**: Run full test suite, lint, type check
3. Create PR 3, merge to main

### Final

1. Complete Phase 15: Polish (T054–T057)
2. Project version is `0.2.0`, all audit findings addressed

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Constitution Principle III requires test-first: write test, verify fail, implement, verify pass
- Commit after each completed user story or logical group
- Stop at any PR checkpoint to validate independently
