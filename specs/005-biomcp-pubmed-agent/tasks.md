# Tasks: BioMCP PubMed Agent

**Input**: Design documents from `/specs/005-biomcp-pubmed-agent/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Tests are required (SC-001 to SC-005 validation). TDD workflow will be followed per Constitution Principle III.

**Organization**: Tasks are organized by user stories for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are absolute from repository root

## Path Conventions

- **LangGraph project**: `langgraph-app/src/agent/`, `langgraph-app/tests/`
- **Main graph**: `langgraph-app/src/agent/graph.py`
- **Node functions**: `langgraph-app/src/agent/nodes/`
- **Models**: `langgraph-app/src/agent/models/`
- **Utils**: `langgraph-app/src/agent/utils/`
- **Tests**: `langgraph-app/tests/unit_tests/nodes/`, `langgraph-app/tests/integration_tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install BioMCP and create directory structure

- [x] T001 Install BioMCP Python package: `uv pip install biomcp-python` in `langgraph-app/`
- [x] T002 Start BioMCP Docker server: `docker run -d -p 8080:8080 --name biomcp genomoncology/biomcp:latest` (used local server: `biomcp run --port 8080`)
- [x] T003 Verify BioMCP health: `curl http://localhost:8080/health`
- [x] T004 [P] Add `BIOMCP_URL=http://localhost:8080` to `langgraph-app/.env`
- [x] T005 [P] Create `langgraph-app/src/agent/utils/` directory (if not exists)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure MUST be complete before ANY user story implementation

**CRITICAL**: No user story work can begin until this phase is complete

### Pydantic Models

- [x] T006 [P] Create `ResearchQuery` Pydantic model in `langgraph-app/src/agent/models/research_models.py`
- [x] T007 [P] Create `PubMedArticle` Pydantic model in `langgraph-app/src/agent/models/research_models.py`
- [x] T008 [P] Create `TranslatedArticle` Pydantic model (inherits PubMedArticle) in `langgraph-app/src/agent/models/research_models.py`
- [x] T009 [P] Create `CitationReference` Pydantic model in `langgraph-app/src/agent/models/research_models.py`

### State Extension

- [x] T010 Update `State` dataclass in `langgraph-app/src/agent/graph.py` - add `research_query: Optional[ResearchQuery]` field
- [x] T011 Add import for `ResearchQuery` from `agent.models.research_models` in `langgraph-app/src/agent/graph.py`

### Translation Prompts

- [x] T012 [P] Create `CZ_TO_EN_PROMPT` template in `langgraph-app/src/agent/utils/translation_prompts.py`
- [x] T013 [P] Create `EN_TO_CZ_PROMPT` template in `langgraph-app/src/agent/utils/translation_prompts.py`

### Test Fixtures

- [x] T014 [P] Add `mock_biomcp_article` fixture in `langgraph-app/tests/conftest.py`
- [x] T015 [P] Add `mock_biomcp_client` fixture in `langgraph-app/tests/conftest.py`
- [x] T016 [P] Add `sample_research_query` fixture in `langgraph-app/tests/conftest.py`
- [x] T017 [P] Add `sample_pubmed_articles` fixture (5 articles) in `langgraph-app/tests/conftest.py`

### Helper Functions (Stubs for TDD)

- [x] T018 Create query classifier stub `classify_research_query()` in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [x] T019 Create document transformer stub `article_to_document()` in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [x] T020 Create citation formatter stub `format_citation()` in `langgraph-app/src/agent/nodes/pubmed_agent.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Basic PubMed Article Search (Priority: P1) MVP

**Goal**: Physician searches PubMed with Czech query and receives 5 relevant articles with Czech abstracts

**Independent Test**: Query "Jaké jsou nejnovější studie o diabetu typu 2?" returns 5 PubMed articles with Czech summaries

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T021 [P] [US1] Unit test for `translate_cz_to_en_node()` basic translation in `langgraph-app/tests/unit_tests/nodes/test_translation.py::TestCzToEnTranslation`
- [x] T022 [P] [US1] Unit test for medical term preservation in `langgraph-app/tests/unit_tests/nodes/test_translation.py::TestMedicalTermPreservation`
- [x] T023 [P] [US1] Unit test for abbreviation expansion in `langgraph-app/tests/unit_tests/nodes/test_translation.py::TestAbbreviationExpansion`
- [x] T024 [P] [US1] Unit test for empty messages error in `langgraph-app/tests/unit_tests/nodes/test_translation.py::TestTranslationErrors`
- [x] T025 [P] [US1] Unit test for PubMed search in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestPubMedSearch`
- [x] T026 [P] [US1] Unit test for no results handling in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestNoResults`
- [x] T027 [P] [US1] Unit test for BioMCP timeout fallback in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestErrorHandling`
- [x] T028 [P] [US1] Integration test for full CZ→EN→PubMed→EN→CZ flow in `langgraph-app/tests/integration_tests/test_pubmed_agent_flow.py::TestFullTranslationFlow`

### Implementation for User Story 1

#### Translation Nodes

- [x] T029 [P] [US1] Implement `translate_cz_to_en_node()` async function in `langgraph-app/src/agent/nodes/translation.py`
- [x] T030 [P] [US1] Implement `translate_en_to_cz_node()` async function in `langgraph-app/src/agent/nodes/translation.py`

#### PubMed Agent Node

- [x] T031 [US1] Implement `classify_research_query()` helper (keyword detection) in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [x] T032 [US1] Implement `_search_pubmed_articles()` helper (BioMCP article_searcher call) in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [x] T033 [US1] Implement `article_to_document()` transformer in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [x] T034 [US1] Implement main `pubmed_agent_node()` async function with search flow in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [x] T035 [US1] Add logging at node entry/exit for all 3 nodes (translate_cz_to_en, pubmed_agent, translate_en_to_cz)

#### Graph Integration

- [x] T036 [US1] Add `RESEARCH_KEYWORDS` set to `langgraph-app/src/agent/graph.py`
- [x] T037 [US1] Extend `route_query()` function with research keyword detection in `langgraph-app/src/agent/graph.py`
- [x] T038 [US1] Add `translate_cz_to_en_node` to graph in `langgraph-app/src/agent/graph.py`
- [x] T039 [US1] Add `pubmed_agent_node` to graph in `langgraph-app/src/agent/graph.py`
- [x] T040 [US1] Add `translate_en_to_cz_node` to graph in `langgraph-app/src/agent/graph.py`
- [x] T041 [US1] Add routing edges: route_query → pubmed_agent → translate_cz_to_en → translate_en_to_cz → __end__
- [x] T042 [US1] Export nodes via `langgraph-app/src/agent/nodes/__init__.py`
- [x] T043 [US1] Export models via `langgraph-app/src/agent/models/__init__.py`

**Checkpoint**: User Story 1 (MVP) is fully functional and testable - physicians can search PubMed with Czech queries

---

## Phase 4: User Story 2 - Article Details and Full Text Access (Priority: P2)

**Goal**: Physician requests detailed information about a specific article by PMID

**Independent Test**: Request "Show me PMID:12345678" returns complete article metadata with Czech abstract

### Tests for User Story 2

- [ ] T044 [P] [US2] Unit test for PMID pattern detection in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestPMIDLookup`
- [ ] T045 [P] [US2] Unit test for `article_getter` tool call in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestArticleGetter`
- [ ] T046 [P] [US2] Unit test for PMC full-text link detection in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestPMCAccess`
- [ ] T047 [P] [US2] Unit test for paywall indication in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestPaywallHandling`
- [ ] T048 [P] [US2] Integration test for PMID lookup flow in `langgraph-app/tests/integration_tests/test_pubmed_agent_flow.py::TestPMIDFlow`

### Implementation for User Story 2

- [ ] T049 [US2] Extend `classify_research_query()` with PMID regex pattern detection in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [ ] T050 [US2] Implement `_get_article_by_pmid()` helper (BioMCP article_getter call) in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [ ] T051 [US2] Implement `_check_pmc_availability()` helper (PMC free full-text detection) in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [ ] T052 [US2] Extend `pubmed_agent_node()` to handle query_type="pmid_lookup" in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [ ] T053 [US2] Add PubMed/PMC URL formatting in `article_to_document()` metadata

**Checkpoint**: User Stories 1 AND 2 are independently functional - physicians can both search and lookup specific articles

---

## Phase 5: User Story 3 - Citation Tracking and Source Verification (Priority: P3)

**Goal**: Physician verifies sources with inline citations [1][2][3] and References section with PubMed URLs

**Independent Test**: Multi-article response shows inline [1][2][3] citations and References section with clickable URLs

### Tests for User Story 3

- [ ] T054 [P] [US3] Unit test for `format_citation()` short citation format in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestCitationFormatting`
- [ ] T055 [P] [US3] Unit test for full citation generation in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestCitationFormatting`
- [ ] T056 [P] [US3] Unit test for citation numbering in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestCitationNumbering`
- [ ] T057 [P] [US3] Unit test for PubMed URL validation in `langgraph-app/tests/unit_tests/nodes/test_pubmed_agent.py::TestURLValidation`
- [ ] T058 [P] [US3] Integration test for citation tracking across queries in `langgraph-app/tests/integration_tests/test_pubmed_agent_flow.py::TestCitationTracking`

### Implementation for User Story 3

- [ ] T059 [US3] Implement `format_citation()` helper (short_citation + full_citation) in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [ ] T060 [US3] Implement `_build_references_section()` helper (format all citations as numbered list) in `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [ ] T061 [US3] Extend `pubmed_agent_node()` to generate inline citations [N] in response message
- [ ] T062 [US3] Add References section formatting to response message in `pubmed_agent_node()`
- [ ] T063 [US3] Ensure all Documents have metadata.url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" (SC-004: 100% auditability)

**Checkpoint**: All user stories are independently functional - complete PubMed agent with citation tracking

---

## Phase 6: Integration Tests & Edge Cases

**Purpose**: Cross-story validation and edge case handling

- [ ] T064 [P] Integration test for date filter queries in `langgraph-app/tests/integration_tests/test_pubmed_agent_flow.py::TestDateFilters`
- [ ] T065 [P] Integration test for BioMCP failure graceful degradation in `langgraph-app/tests/integration_tests/test_pubmed_agent_flow.py::TestFailureHandling`
- [ ] T066 [P] Integration test for multi-query citation numbering continuity in `langgraph-app/tests/integration_tests/test_pubmed_agent_flow.py::TestCitationContinuity`
- [ ] T067 [P] Performance benchmark test for <5s latency (SC-001) in `langgraph-app/tests/performance/test_pubmed_latency.py`
- [ ] T068 [P] Translation quality test for 95% semantic preservation (SC-002) - manual validation checklist

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, verification, and final quality checks

- [ ] T069 [P] Update `langgraph-app/src/agent/models/__init__.py` with all ResearchQuery exports
- [ ] T070 [P] Update `langgraph-app/src/agent/nodes/__init__.py` with all pubmed_agent exports
- [ ] T071 [P] Add docstrings to all node functions (Google style per CLAUDE.md)
- [ ] T072 [P] Add type hints validation: `mypy --strict langgraph-app/src/agent/nodes/pubmed_agent.py`
- [ ] T073 [P] Add type hints validation: `mypy --strict langgraph-app/src/agent/nodes/translation.py`
- [ ] T074 [P] Run linting: `make lint` in `langgraph-app/`
- [ ] T075 [P] Run formatting: `make format` in `langgraph-app/`
- [ ] T076 Verify LangGraph Studio visualization shows pubmed_agent node with 3 sub-nodes
- [ ] T077 Run full test suite: `make test` - verify all 35 tests passing (12 translation + 15 pubmed_agent + 8 integration)
- [ ] T078 Validate quickstart.md manual test scenarios (3 test queries)
- [ ] T079 LangSmith trace analysis - verify <5s latency for 90% queries (SC-001)
- [ ] T080 Update `specs/005-biomcp-pubmed-agent/tasks.md` - mark all tasks complete ✓
- [ ] T081 Commit all changes: `git add . && git commit -m "feat(pubmed): complete BioMCP PubMed Agent implementation"`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Integration Tests (Phase 6)**: Depends on all desired user stories being complete
- **Polish (Phase 7)**: Depends on Integration Tests completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 `pubmed_agent_node()` but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Extends US1/US2 citation formatting but independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation (TDD per Constitution Principle III)
- Models before helpers
- Helpers before main node function
- Node function before graph integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks (T001-T005) marked [P] can run in parallel
- All Foundational Pydantic models (T006-T009) marked [P] can run in parallel
- All Foundational prompts (T012-T013) marked [P] can run in parallel
- All Foundational fixtures (T014-T017) marked [P] can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Translation nodes (T029-T030) marked [P] can be implemented in parallel
- All Polish tasks (T069-T075) marked [P] can run in parallel

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all US1 tests together (they should all FAIL initially):
Task T021: "Unit test for translate_cz_to_en_node basic translation"
Task T022: "Unit test for medical term preservation"
Task T023: "Unit test for abbreviation expansion"
Task T024: "Unit test for empty messages error"
Task T025: "Unit test for PubMed search"
Task T026: "Unit test for no results handling"
Task T027: "Unit test for BioMCP timeout fallback"
Task T028: "Integration test for full translation flow"

# Then implement in sequence:
Task T029: "Implement translate_cz_to_en_node"
Task T030: "Implement translate_en_to_cz_node"
Task T031: "Implement classify_research_query"
# ... etc.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T020) - CRITICAL blocker
3. Complete Phase 3: User Story 1 (T021-T043)
4. **STOP and VALIDATE**: Test User Story 1 independently with manual queries
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP: Basic PubMed search!)
3. Add User Story 2 → Test independently → Deploy/Demo (Add PMID lookup)
4. Add User Story 3 → Test independently → Deploy/Demo (Add citation tracking)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T020)
2. Once Foundational is done:
   - Developer A: User Story 1 (T021-T043)
   - Developer B: User Story 2 (T044-T053)
   - Developer C: User Story 3 (T054-T063)
3. Stories complete and integrate independently
4. Team runs Integration Tests (T064-T068) together
5. Team completes Polish (T069-T081) together

---

## Notes

- **TDD Workflow**: Write test → Verify FAIL → Implement → Verify PASS (Constitution Principle III)
- **[P] tasks**: Different files, no dependencies, can run in parallel
- **[Story] label**: Maps task to specific user story for traceability
- **Translation Pattern**: "Sandwich Pattern" (CZ → EN → PubMed → EN → CZ)
- **Performance Target**: <5s for 90% queries (SC-001) - verify with LangSmith traces
- **Cost Target**: $0.001 per query - monitor token usage
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Use LangGraph Studio for visual debugging of graph flow

---

## Success Validation Checklist

After completing all phases, verify:

- [ ] SC-001: Physicians retrieve articles in <5s for 90% of queries (measure with LangSmith)
- [ ] SC-002: Czech medical queries translated with 95% semantic preservation (manual expert review)
- [ ] SC-003: 80% of physicians find relevant article on first search (user testing)
- [ ] SC-004: Every article has verifiable PubMed URL (metadata.url check)
- [ ] SC-005: BioMCP failures handled gracefully with Czech error messages (integration tests)
- [ ] All 35 tests passing (12 translation + 15 pubmed_agent + 8 integration)
- [ ] LangGraph Studio shows complete pubmed_agent node with translation flow
- [ ] `mypy --strict` passes for all new files
- [ ] Manual testing with 3 quickstart.md scenarios successful

**Estimated Total Time**: 8-10 hours (with TDD)
**Total Tasks**: 81
