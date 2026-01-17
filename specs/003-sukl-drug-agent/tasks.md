# Tasks: SÚKL Drug Agent

**Input**: Design documents from `/specs/003-sukl-drug-agent/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Testy jsou požadovány (SC-006: ≥90% pokrytí). TDD workflow bude dodržen.

**Organization**: Úkoly jsou organizovány podle user stories pro nezávislou implementaci a testování.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Může běžet paralelně (různé soubory, žádné závislosti)
- **[Story]**: Ke které user story úkol patří (US1, US2, US3, US4, US5)
- Cesty k souborům jsou absolutní od kořene repozitáře

## Path Conventions

- **LangGraph project**: `langgraph-app/src/agent/`, `langgraph-app/tests/`
- **Main graph**: `langgraph-app/src/agent/graph.py`
- **Node functions**: `langgraph-app/src/agent/nodes/`
- **Models**: `langgraph-app/src/agent/models/`
- **Tests**: `langgraph-app/tests/unit_tests/nodes/`, `langgraph-app/tests/integration_tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Vytvoření adresářové struktury a základní konfigurace

- [x] T001 Create `langgraph-app/src/agent/nodes/` directory
- [x] T002 Create `langgraph-app/src/agent/models/` directory
- [x] T003 [P] Create `langgraph-app/src/agent/nodes/__init__.py` with exports
- [x] T004 [P] Create `langgraph-app/src/agent/models/__init__.py` with exports
- [x] T005 [P] Create `langgraph-app/tests/unit_tests/nodes/` directory
- [x] T006 [P] Create `langgraph-app/tests/unit_tests/nodes/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Základní infrastruktura MUSÍ být hotová před implementací user stories

**CRITICAL**: Žádná práce na user stories nesmí začít, dokud není tato fáze dokončena

### Pydantic Models

- [x] T007 [P] Create `QueryType` enum in `langgraph-app/src/agent/models/drug_models.py`
- [x] T008 [P] Create `DrugQuery` Pydantic model in `langgraph-app/src/agent/models/drug_models.py`
- [x] T009 [P] Create `DrugResult` Pydantic model in `langgraph-app/src/agent/models/drug_models.py`
- [x] T010 [P] Create `DrugDetails` Pydantic model in `langgraph-app/src/agent/models/drug_models.py`
- [x] T011 [P] Create `ReimbursementInfo` Pydantic model in `langgraph-app/src/agent/models/drug_models.py`
- [x] T012 [P] Create `AvailabilityInfo` Pydantic model in `langgraph-app/src/agent/models/drug_models.py`

### State Extension

- [x] T013 Update `State` dataclass in `langgraph-app/src/agent/graph.py` - add `drug_query: Optional[DrugQuery]` field
- [x] T014 Add import for `DrugQuery` in `langgraph-app/src/agent/graph.py`

### Test Fixtures

- [x] T015 [P] Add `mock_sukl_response` fixture in `langgraph-app/tests/conftest.py`
- [x] T016 [P] Add `mock_sukl_client` fixture in `langgraph-app/tests/conftest.py`
- [x] T017 [P] Add `sample_drug_query` fixture in `langgraph-app/tests/conftest.py`

### Helper Functions

- [x] T018 Create query classifier function `classify_drug_query()` in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T019 Create document transformer `drug_result_to_document()` in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T020 Create error message formatter `format_mcp_error()` in `langgraph-app/src/agent/nodes/drug_agent.py`

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Vyhledávání léku podle názvu (Priority: P1) MVP

**Goal**: Uživatel může vyhledat lék podle názvu s fuzzy matching

**Independent Test**: Zadáním názvu léku (např. "Ibalgin") systém vrátí seznam odpovídajících léků

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T021 [P] [US1] Unit test for drug search in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestDrugSearch`
- [x] T022 [P] [US1] Unit test for fuzzy matching in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestFuzzyMatching`
- [x] T023 [P] [US1] Unit test for empty results in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestNoResults`

### Implementation for User Story 1

- [x] T024 [US1] Implement `_search_drugs()` helper in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T025 [US1] Implement main `drug_agent_node()` async function in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T026 [US1] Add drug_agent_node to graph in `langgraph-app/src/agent/graph.py` (export via nodes/__init__.py)
- [x] T027 [US1] Add logging at node entry/exit in `langgraph-app/src/agent/nodes/drug_agent.py`

**Checkpoint**: User Story 1 (MVP) je plně funkční a testovatelná

---

## Phase 4: User Story 2 - Detailní informace o léku (Priority: P1)

**Goal**: Uživatel získá kompletní detaily o konkrétním léku

**Independent Test**: Zadáním registračního čísla systém vrátí složení, indikace, kontraindikace

### Tests for User Story 2

- [x] T028 [P] [US2] Unit test for drug details in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestDrugDetails`
- [x] T029 [P] [US2] Unit test for details document format in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestDocumentTransformers`

### Implementation for User Story 2

- [x] T030 [US2] Implement `_get_drug_details()` helper in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T031 [US2] Implement `drug_details_to_document()` transformer in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T032 [US2] Extend `drug_agent_node()` to handle details queries in `langgraph-app/src/agent/nodes/drug_agent.py`

**Checkpoint**: User Stories 1 AND 2 jsou nezávisle funkční

---

## Phase 5: User Story 3 - Informace o úhradě (Priority: P2)

**Goal**: Uživatel získá informace o úhradě léku a cenách

**Independent Test**: Dotazem na lék systém vrátí kategorii úhrady a doplatek

### Tests for User Story 3

- [x] T033 [P] [US3] Unit test for reimbursement info in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestDocumentTransformers`
- [x] T034 [P] [US3] Unit test for category formatting in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestDocumentTransformers`

### Implementation for User Story 3

- [x] T035 [US3] Implement `_get_reimbursement()` helper in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T036 [US3] Implement `reimbursement_to_document()` transformer in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T037 [US3] Extend `drug_agent_node()` to handle reimbursement queries

**Checkpoint**: User Stories 1, 2, AND 3 jsou nezávisle funkční

---

## Phase 6: User Story 4 - Kontrola dostupnosti (Priority: P2)

**Goal**: Uživatel ověří dostupnost léku a získá alternativy

**Independent Test**: Dotazem na nedostupný lék systém vrátí alternativy

### Tests for User Story 4

- [x] T038 [P] [US4] Unit test for availability check in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestDocumentTransformers`
- [x] T039 [P] [US4] Unit test for alternatives in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestDocumentTransformers`

### Implementation for User Story 4

- [x] T040 [US4] Implement `_check_availability()` helper in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T041 [US4] Implement `availability_to_document()` transformer in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T042 [US4] Extend `drug_agent_node()` to handle availability queries

**Checkpoint**: User Stories 1-4 jsou všechny nezávisle funkční

---

## Phase 7: User Story 5 - ATC/Ingredient Search (Priority: P3)

**Goal**: Uživatel vyhledá léky podle ATC kódu nebo účinné látky

**Independent Test**: Zadáním ATC kódu nebo názvu účinné látky systém vrátí seznam léků

### Tests for User Story 5

- [x] T043 [P] [US5] Unit test for ATC search in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestQueryClassification`
- [x] T044 [P] [US5] Unit test for ingredient search in `langgraph-app/tests/unit_tests/nodes/test_drug_agent.py::TestQueryClassification`

### Implementation for User Story 5

- [x] T045 [US5] Implement `_search_by_atc()` helper in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T046 [US5] Implement `_search_by_ingredient()` helper in `langgraph-app/src/agent/nodes/drug_agent.py`
- [x] T047 [US5] Extend `drug_agent_node()` to handle ATC/ingredient queries

**Checkpoint**: Všechny user stories jsou nezávisle funkční

---

## Phase 8: Integration Tests

**Purpose**: End-to-end testování celého flow

- [ ] T048 [P] Create integration test file `langgraph-app/tests/integration_tests/test_drug_agent_flow.py`
- [ ] T049 [P] Integration test for search → details flow in `test_drug_agent_flow.py`
- [ ] T050 Integration test for error handling (timeout, connection error) in `test_drug_agent_flow.py`
- [ ] T051 Integration test for full graph execution with drug_agent_node

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Finalizace a dokumentace

- [x] T052 [P] Export `drug_agent_node` from `langgraph-app/src/agent/nodes/__init__.py`
- [x] T053 [P] Export models from `langgraph-app/src/agent/models/__init__.py`
- [x] T054 Update `langgraph-app/src/agent/__init__.py` with new exports
- [x] T055 [P] Run `mypy --strict` on all new files
- [x] T056 [P] Run `ruff` linting on all new files
- [ ] T057 Verify LangGraph Studio visualization
- [x] T058 Run full test suite (150 tests passing, 59% coverage - integration tests needed for 90%)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Žádné závislosti - může začít okamžitě
- **Foundational (Phase 2)**: Závisí na Setup - BLOKUJE všechny user stories
- **User Stories (Phase 3-7)**: Všechny závisí na Foundational
  - Mohou pokračovat paralelně (pokud jsou dostupné zdroje)
  - Nebo sekvenčně podle priority (P1 → P1 → P2 → P2 → P3)
- **Integration (Phase 8)**: Závisí na dokončení všech user stories
- **Polish (Phase 9)**: Závisí na dokončení integračních testů

### User Story Dependencies

- **User Story 1 (P1)**: Může začít po Foundational - žádné závislosti na jiných stories
- **User Story 2 (P1)**: Může začít po Foundational - nezávislé na US1
- **User Story 3 (P2)**: Může začít po Foundational - nezávislé na US1/US2
- **User Story 4 (P2)**: Může začít po Foundational - nezávislé
- **User Story 5 (P3)**: Může začít po Foundational - nezávislé

### Within Each User Story

1. Testy MUSÍ být napsány a SELHÁVAT před implementací (TDD)
2. Helper funkce před hlavním node
3. Node implementace před integrací do grafu
4. Story kompletní před přechodem na další prioritu

### Parallel Opportunities

- T003-T006: Setup soubory paralelně
- T007-T012: Všechny Pydantic modely paralelně
- T015-T017: Všechny fixtures paralelně
- T021-T023: Testy pro US1 paralelně
- Po Foundational: Všechny user stories mohou začít paralelně

---

## Parallel Example: Foundational Phase

```bash
# Launch all Pydantic models together:
Task: "Create QueryType enum in langgraph-app/src/agent/models/drug_models.py"
Task: "Create DrugQuery Pydantic model in langgraph-app/src/agent/models/drug_models.py"
Task: "Create DrugResult Pydantic model in langgraph-app/src/agent/models/drug_models.py"
Task: "Create DrugDetails Pydantic model in langgraph-app/src/agent/models/drug_models.py"
Task: "Create ReimbursementInfo Pydantic model in langgraph-app/src/agent/models/drug_models.py"
Task: "Create AvailabilityInfo Pydantic model in langgraph-app/src/agent/models/drug_models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Search)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready - základní vyhledávání léků funguje!

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Deploy (MVP: vyhledávání)
3. Add User Story 2 → Test → Deploy (detaily léků)
4. Add User Story 3 → Test → Deploy (úhrady)
5. Add User Story 4 → Test → Deploy (dostupnost)
6. Add User Story 5 → Test → Deploy (ATC/ingredient)
7. Integration Tests + Polish → Final release

### Sequential Execution (Single Developer)

1. Phase 1 → Phase 2 → Phase 3 (MVP checkpoint)
2. Phase 4 → Phase 5 → Phase 6 → Phase 7
3. Phase 8 → Phase 9

---

## Summary

| Phase | Tasks | Parallel Tasks | User Story |
|-------|-------|----------------|------------|
| Setup | 6 | 4 | - |
| Foundational | 14 | 11 | - |
| US1 (MVP) | 7 | 3 | P1 |
| US2 | 5 | 2 | P1 |
| US3 | 5 | 2 | P2 |
| US4 | 5 | 2 | P2 |
| US5 | 5 | 2 | P3 |
| Integration | 4 | 2 | - |
| Polish | 7 | 4 | - |
| **TOTAL** | **58** | **32** | - |

**MVP Scope**: Phase 1 + 2 + 3 = 27 tasks
**Full Feature**: 58 tasks

---

## Notes

- [P] tasks = různé soubory, žádné závislosti
- [Story] label mapuje úkol na specifickou user story
- Každá user story je nezávisle dokončitelná a testovatelná
- TDD workflow: Verify tests fail before implementing
- Commit po každém úkolu nebo logické skupině
- Stop at any checkpoint to validate story independently
