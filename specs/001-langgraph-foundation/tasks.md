# Tasks: LangGraph Foundation

**Input**: Design documents from `/specs/001-langgraph-foundation/`  
**Prerequisites**: spec.md (DONE), plan.md (DONE)

**Organization**: Tasks grouped by user story for independent implementation

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1-US5)
- Include exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency management

- [ ] T001 Install additional dependencies: `langchain-core`, `pytest-asyncio`, `langsmith`
- [ ] T002 [P] Create `.env.example` file with LangSmith configuration template
- [ ] T003 [P] Update `.gitignore` to exclude `.env` file if not already present

**Checkpoint**: Dependencies installed, environment template ready

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core type definitions that all code depends on

### Tests for Foundation (Test-First Approach) ⚠️

> **CRITICAL**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T004 [P] [US1] Create `langgraph-app/tests/unit_tests/__init__.py`
- [ ] T005 [P] [US1] Create `langgraph-app/tests/integration_tests/__init__.py`
- [ ] T006 [US3] Write failing test in `tests/unit_tests/test_foundation.py` for `placeholder_node` echoing messages
- [ ] T007 [US3] Write failing test in `tests/unit_tests/test_foundation.py` for `placeholder_node` handling empty state
- [ ] T008 [US3] Write failing test in `tests/integration_tests/test_graph_foundation.py` for graph invocation
- [ ] T009 [US3] Write failing test in `tests/integration_tests/test_graph_foundation.py` for graph rendering

**Checkpoint**: All tests written and FAILING (red state)

---

## Phase 3: User Story 1 - Define Agent State Schema (Priority: P1) 🎯

**Goal**: Create strongly-typed AgentState with messages, next, retrieved_docs

**Independent Test**: Can instantiate AgentState without type errors

### Implementation for US1

- [ ] T010 [US1] Define `State` dataclass in `langgraph-app/src/agent/graph.py` with typed fields
- [ ] T011 [US1] Add `add_messages` reducer annotation to `messages` field
- [ ] T012 [US1] Implement `__post_init__` for mutable default (`retrieved_docs`)
- [ ] T013 [US1] Add Google-style docstring to `State` class
- [ ] T014 [US1] Run `mypy --strict langgraph-app/src/agent/graph.py` and fix type errors

**Checkpoint**: State schema defined, mypy passes

---

## Phase 4: User Story 2 - Configure Runtime Context (Priority: P1) 🎯

**Goal**: Create Context TypedDict for runtime configuration (with BioAgents-inspired extensions)

**Independent Test**: Can pass Context to graph invocation

### Implementation for US2

- [ ] T015 [P] [US2] Import `Literal` from `typing` module
- [ ] T016 [P] [US2] Define `Context` TypedDict in `langgraph-app/src/agent/graph.py`
- [ ] T017 [P] [US2] Add core fields: `model_name`, `temperature`, `langsmith_project`, `user_id`
- [ ] T018 [P] [US2] Add MCP client placeholder fields: `sukl_mcp_client`, `biomcp_client` (type: `Any`)
- [ ] T019 [P] [US2] Add conversation persistence field: `conversation_context` (type: `Any`)
- [ ] T020 [P] [US2] Add workflow mode field: `mode` (type: `Literal["quick", "deep"]`)
- [ ] T021 [P] [US2] Set `total=False` for optional fields
- [ ] T022 [P] [US2] Add comprehensive Google-style docstring with field groups

**Note**: MCP client fields (`sukl_mcp_client`, `biomcp_client`) are placeholders typed as `Any` in this feature. Proper typing happens in Feature 002 (MCP Infrastructure). `conversation_context` is implemented in Feature 013 (Workflow Modes).

**Checkpoint**: Context schema defined with all fields and documented

---

## Phase 5: User Story 3 - Setup Pytest Testing Infrastructure (Priority: P1) 🎯

**Goal**: Create reusable pytest fixtures (with extended Context support)

**Independent Test**: Can use fixtures in new tests

### Implementation for US3

- [ ] T023 [US3] Create `langgraph-app/tests/conftest.py` with pytest fixtures
- [ ] T024 [US3] Implement `sample_state` fixture returning valid State instance
- [ ] T025 [US3] Implement `mock_runtime` fixture with complete mock Context including:
  - Core fields (`model_name`, `temperature`, `langsmith_project`)
  - Mock MCP clients (`sukl_mcp_client=None`, `biomcp_client=None`)
  - Mock conversation context (`conversation_context=None`)
  - Default mode (`mode="quick"`)
- [ ] T026 [US3] Implement `test_graph` fixture for integration tests
- [ ] T027 [US3] Add docstrings to all fixtures
- [ ] T028 [US3] Run `pytest --collect-only` to verify fixtures are discovered

**Note**: Mock MCP clients set to `None` in fixtures since Feature 001 doesn't implement actual clients. Real mock clients will be added in Feature 002 test fixtures.

**Checkpoint**: Fixtures available with all Context fields and discoverable

---

## Phase 6: User Story 5 - Create Base Graph Structure (Priority: P1) 🎯

**Goal**: Build minimal working graph with placeholder node

**Independent Test**: Graph compiles and executes successfully

### Implementation for US5

- [ ] T029 [US5] Implement `placeholder_node` async function in `langgraph-app/src/agent/graph.py`
- [ ] T030 [US5] Add logging at node entry/exit with `print()` statements
- [ ] T031 [US5] Implement echo logic for last user message
- [ ] T032 [US5] Add Google-style docstring to `placeholder_node`
- [ ] T033 [US5] Create `StateGraph` instance with `State` and `context_schema=Context`
- [ ] T034 [US5] Add "placeholder" node to graph with `.add_node()`
- [ ] T035 [US5] Add edges: `__start__ -> placeholder -> __end__`
- [ ] T036 [US5] Compile graph with name "Czech MedAI Foundation"
- [ ] T037 [US5] Export `graph` variable for imports

**Checkpoint**: Graph compiles without errors, placeholder node implemented

---

## Phase 7: User Story 4 - Integrate LangSmith Tracing (Priority: P2) 🎯

**Goal**: Enable LangSmith tracing with graceful degradation

**Independent Test**: Traces appear in LangSmith dashboard when API key set

### Implementation for US4

- [ ] T038 [P] [US4] Add `python-dotenv` import to `langgraph-app/src/agent/graph.py`
- [ ] T039 [P] [US4] Load environment variables with `load_dotenv()` at module level
- [ ] T040 [US4] Add try/except around LangSmith initialization
- [ ] T041 [US4] Log warning if LangSmith tracing fails to initialize
- [ ] T042 [US4] Verify tracing works by invoking graph with `.env` file configured

**Checkpoint**: LangSmith tracing enabled with graceful degradation

---

## Phase 8: Testing & Validation

**Purpose**: Ensure all tests pass and quality gates met

- [ ] T043 Run `pytest langgraph-app/tests/unit_tests/test_foundation.py -v`
- [ ] T044 Run `pytest langgraph-app/tests/integration_tests/test_graph_foundation.py -v`
- [ ] T045 Verify test coverage ≥80% with `pytest --cov=langgraph-app/src --cov-report=term`
- [ ] T046 Run `ruff check langgraph-app/src/` and fix all linting errors
- [ ] T047 Run `mypy --strict langgraph-app/src/agent/graph.py` and verify zero errors
- [ ] T048 Verify all docstrings pass D401 rule (imperative mood)

**Checkpoint**: All tests GREEN, linting passed, type checking passed

---

## Phase 9: Manual Verification

**Purpose**: Validate in LangGraph Studio and LangSmith

- [ ] T049 Start LangGraph Studio and open project
- [ ] T050 Verify graph renders with "placeholder" node visible
- [ ] T051 Invoke graph in Studio and verify response
- [ ] T052 Check LangSmith dashboard for execution traces (if API key set)
- [ ] T053 Verify state transitions logged in console output

**Checkpoint**: Manual verification complete

---

## Phase 10: Documentation

**Purpose**: Update project documentation

- [ ] T054 [P] Update `langgraph-app/README.md` with foundation setup instructions
- [ ] T055 [P] Add section on running tests
- [ ] T056 [P] Add section on LangSmith configuration
- [ ] T057 [P] Document State and Context schemas with examples (including new BioAgents-inspired fields)

**Checkpoint**: Documentation updated

---

## Definition of Done

✅ **All tasks completed**  
✅ **All tests passing** (pytest exit code 0)  
✅ **Test coverage ≥80%**  
✅ **Zero linting errors** (ruff exit code 0)  
✅ **Zero type errors** (mypy exit code 0)  
✅ **Graph renders in Studio**  
✅ **LangSmith traces visible** (if configured)  
✅ **Documentation updated**  
✅ **Git commit with message**: `feat: implement LangGraph foundation (001)`

---

## Estimated Timeline

- **Phase 1-2**: 0.5 days (setup + failing tests)
- **Phase 3-4**: 2 days (State + extended Context implementation with BioAgents fields)
- **Phase 5-6**: 1.5 days (fixtures + graph structure)
- **Phase 7**: 0.5 days (LangSmith integration)
- **Phase 8**: 1 day (testing & validation)
- **Phase 9**: 0.5 days (manual verification)
- **Phase 10**: 0.5 days (documentation)

**Total**: ~6 days (extended from original 5 days due to BioAgents-inspired Context extensions)

**Note**: Added 8 tasks for extended Context schema (MCP clients, conversation_context, workflow mode). Most are type definitions with minimal implementation overhead in this foundation feature.

---

## Next Actions

1. Start with Phase 1: `pip install langchain-core pytest-asyncio langsmith`
2. Create `.env.example` file
3. Write FAILING tests in Phase 2 (test-first approach)
4. Implement State/Context (Phase 3-4)
5. Continue through phases sequentially

**Ready to begin implementation!** 🚀
