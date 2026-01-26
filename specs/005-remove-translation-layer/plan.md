# Implementation Plan: Feature 005 Refactoring - Remove Translation Layer

**Feature**: Odstranění Translation Sandwich Pattern
**Branch**: `005-biomcp-pubmed-agent`
**Spec**: [spec.md](./spec.md)
**Status**: Planning
**Created**: 2026-01-25

---

## Executive Summary

**Objective**: Zjednodušit PubMed agent odstraněním zbytečného translation layer (CZ→EN→PubMed→EN→CZ) a využít nativní multilingvní capabilities Claude Sonnet 4.5.

**Key Changes**:
- Remove 2 translation nodes from graph (`translate_cz_to_en`, `translate_en_to_cz`)
- Update PubMed agent pro direct Czech query processing
- Eliminate ANTHROPIC_API_KEY dependency
- Simplify routing: `route_query` → `pubmed_agent` → `__end__` (bez translation)

**Expected Outcomes**:
- 40-50% latency reduction (8-10s → 5s)
- 66% cost reduction (3 LLM calls → 1 LLM call)
- Simplified graph architecture (3 nodes → 1 node)
- Better Czech language quality (no translation artifacts)

---

## Technical Context

### Current Architecture

```
User Query (CZ)
    ↓
[route_query] - Keyword-based intent classification
    ↓
    ├→ [Drug Agent] → SÚKL-mcp → drug info (CZ)
    ├→ [translate_cz_to_en] → EN query
    │   ↓
    │   [pubmed_agent] → BioMCP (EN) → articles
    │   ↓
    │   [translate_en_to_cz] → CZ results
    └→ [Placeholder] → echo message
    ↓
Response (CZ)
```

**Files Involved:**
- `src/agent/graph.py` - Graph definition with translation edges
- `src/agent/nodes/translation.py` - Translation nodes implementation
- `src/agent/nodes/pubmed_agent.py` - PubMed search logic
- `src/agent/utils/translation_prompts.py` - Translation prompt templates
- `src/agent/models/research_models.py` - ResearchQuery model

**Dependencies:**
- Claude Sonnet 4.5 via Anthropic API (for translation)
- BioMCP client for PubMed access
- LangGraph StateGraph for orchestration

### Target Architecture

```
User Query (CZ)
    ↓
[route_query] - Keyword-based intent classification
    ↓
    ├→ [Drug Agent] → SÚKL-mcp → drug info (CZ)
    ├→ [pubmed_agent] → BioMCP + Claude (CZ) → articles (CZ)
    └→ [Placeholder] → echo message
    ↓
Response (CZ)
```

**Simplified Flow:**
- Direct Czech processing in PubMed agent
- Claude converts English abstracts to Czech inline
- No intermediate translation steps

**Removed Components:**
- `translate_cz_to_en_node`
- `translate_en_to_cz_node`
- Translation edges in graph
- ResearchQuery model dependency
- ANTHROPIC_API_KEY requirement

---

## Constitution Check

### Principle I: Graph-Centric Architecture ✅

**Compliance**: YES
- Refactoring removes nodes and edges from graph (simplifies, doesn't violate)
- PubMed agent remains async node with proper signature
- All business logic stays in graph nodes
- Graph remains visualizable in LangGraph Studio

**Changes**:
- Remove 2 nodes from StateGraph
- Update 2 conditional edges (routing paths)
- Simplify graph visualization

### Principle II: Type Safety & Schema Validation ✅

**Compliance**: YES
- Remove `ResearchQuery` from State (unused after refactoring)
- Maintain typed State and Context
- PubMed agent continues using typed Document returns

**Changes**:
- Remove `research_query: ResearchQuery | None` from State dataclass
- Keep typed message handling in PubMed agent

### Principle III: Test-First Development ✅

**Compliance**: YES
- Update existing tests before code changes
- Maintain test coverage ≥80%
- Follow TDD workflow for each task

**Test Changes Required**:
- Delete translation node tests
- Update PubMed agent tests for Czech input
- Update integration tests for simplified flow
- Maintain routing tests (update expectations)

### Principle IV: Observability & Debugging ✅

**Compliance**: YES
- LangSmith tracing continues (no impact)
- Logging in PubMed agent preserved
- LangGraph Studio visualization updated (simpler graph)

**No Changes Required**: Observability unaffected

### Principle V: Modular & Extensible Design ✅

**Compliance**: YES
- Removing nodes improves modularity (less complexity)
- PubMed agent becomes more focused (single responsibility)
- Context usage unchanged

**Improvement**: Simpler architecture = better modularity

---

## Quality Gates

### Pre-Implementation Checks

- [x] **Spec Complete**: All functional requirements defined
- [x] **Constitution Compliant**: All 5 principles satisfied
- [x] **Test Strategy Defined**: Test updates identified
- [x] **Dependencies Clear**: BioMCP, Claude Sonnet 4.5

### Implementation Gates

- [ ] **Unit Tests Pass**: ≥169/175 passing (maintain coverage)
- [ ] **Type Checking**: `mypy --strict` zero errors
- [ ] **Linting**: `ruff check .` all checks pass
- [ ] **Integration Tests**: Research flow works end-to-end
- [ ] **Performance**: <5s latency for research queries

### Post-Implementation Validation

- [ ] **LangGraph Studio**: Graph visualizes correctly (no translation nodes)
- [ ] **Czech Quality**: Manual validation with Czech doctors
- [ ] **Cost Verification**: API usage reduced by ~66%
- [ ] **Documentation**: CLAUDE.md and README.md updated

---

## Phase 0: Research & Design

### Research Tasks

**R001: Claude Sonnet 4.5 Czech Capabilities** ✅
- **Status**: RESOLVED (no research needed)
- **Finding**: Claude Sonnet 4.5 is state-of-the-art multilingvní model with native Czech support
- **Evidence**: Documented in Anthropic model capabilities
- **Decision**: Use direct Czech processing without translation layer

**R002: BioMCP Query Language Support** ✅
- **Status**: RESOLVED (no research needed)
- **Finding**: BioMCP article_searcher accepts any query string (language-agnostic)
- **Evidence**: BioMCP API documentation - uses keyword extraction
- **Decision**: Send Czech queries directly to BioMCP

**R003: Citation Preservation Without Translation** ✅
- **Status**: RESOLVED (architectural review)
- **Finding**: Citation format [1][2][3] is generated by PubMed agent, not translation layer
- **Evidence**: Code review of pubmed_agent.py - citations added post-retrieval
- **Decision**: Citations will work unchanged

### Design Artifacts

**No new artifacts required** - This is a refactoring (removal) task.

Existing artifacts affected:
- Graph structure simplified
- State schema reduced (remove ResearchQuery)
- No new data models

---

## Phase 1: Implementation Planning

### Graph Changes

#### Node Removal

**Nodes to Delete:**
1. `translate_cz_to_en` - Translation node (CZ→EN)
2. `translate_en_to_cz` - Translation node (EN→CZ)

**Impact:**
- Graph complexity reduced from 5 nodes to 3 nodes (research flow)
- 2 fewer node function definitions
- Simplified LangGraph Studio visualization

#### Edge Updates

**Current Edges (Research Flow):**
```python
.add_conditional_edges(
    "route_query",
    lambda state: state["next"],
    {
        "translate_cz_to_en": "translate_cz_to_en",  # Research path
        "drug_agent": "drug_agent",
        "__end__": "__end__"
    }
)
.add_edge("translate_cz_to_en", "pubmed_agent")
.add_edge("pubmed_agent", "translate_en_to_cz")
.add_edge("translate_en_to_cz", "__end__")
```

**New Edges (Simplified):**
```python
.add_conditional_edges(
    "route_query",
    lambda state: state["next"],
    {
        "pubmed_agent": "pubmed_agent",  # Direct path
        "drug_agent": "drug_agent",
        "__end__": "__end__"
    }
)
.add_edge("pubmed_agent", "__end__")  # Direct to end
```

**Change Summary:**
- Remove `translate_cz_to_en` from conditional routing
- Change routing target from `"translate_cz_to_en"` to `"pubmed_agent"`
- Remove 3 edges: `translate_cz_to_en → pubmed_agent`, `pubmed_agent → translate_en_to_cz`, `translate_en_to_cz → __end__`
- Add 1 edge: `pubmed_agent → __end__`

#### State Schema Changes

**Remove from State:**
```python
@dataclass
class State:
    # ... existing fields ...
    research_query: ResearchQuery | None = None  # DELETE THIS
```

**Rationale**: `research_query` was populated by `translate_cz_to_en` node. With direct Czech processing, PubMed agent parses query from `state.messages[-1].content` directly.

**No other State changes needed.**

### PubMed Agent Refactoring

#### Current Implementation (Expects English)

```python
async def pubmed_agent_node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    research_query = state.research_query  # Expects EN query from translation
    if not research_query:
        # Error handling

    # Call BioMCP with English query
    articles = await _search_pubmed_articles(research_query, biomcp_client)
    # Return English documents (translation node converts to CZ)
```

#### Target Implementation (Direct Czech)

```python
async def pubmed_agent_node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    # Parse Czech query directly from messages
    last_message = state.messages[-1]
    czech_query = extract_content(last_message)  # Helper function

    # Call BioMCP with Czech query (BioMCP keyword-based, language-agnostic)
    articles = await _search_pubmed_articles_czech(czech_query, biomcp_client)

    # Use Claude to generate Czech summary with citations
    # Claude converts English abstracts to Czech inline
    response = await _generate_czech_response(articles, claude_client)
    return {"messages": [response]}
```

**Key Changes:**
1. Remove dependency on `state.research_query`
2. Parse query from `state.messages` directly
3. Add Claude integration for Czech response generation
4. Convert English abstracts to Czech inline (Claude's job)

### Routing Logic Update

**Current Logic:**
```python
# route_query function
if keyword in RESEARCH_KEYWORDS:
    return "translate_cz_to_en"  # Trigger translation first
```

**New Logic:**
```python
# route_query function
if keyword in RESEARCH_KEYWORDS:
    return "pubmed_agent"  # Direct to PubMed agent
```

**No keyword changes needed** - RESEARCH_KEYWORDS remain unchanged.

### File Deletions

**Files to Delete:**
1. `src/agent/nodes/translation.py` - Translation node implementations
2. `src/agent/utils/translation_prompts.py` - Translation prompt templates
3. `tests/unit_tests/nodes/test_translation.py` - Translation tests

**Import Cleanup:**
- Remove imports from `graph.py`: `translate_cz_to_en_node`, `translate_en_to_cz_node`
- Remove imports from test files referencing translation

---

## Phase 2: Task Breakdown

### Task Categories

**Critical Path (P0):**
1. Update graph definition (remove nodes/edges)
2. Refactor PubMed agent for Czech
3. Update routing logic
4. Update tests

**Supporting (P1):**
5. Delete translation files
6. Update State schema
7. Update documentation

**Cleanup (P2):**
8. Remove ANTHROPIC_API_KEY from .env
9. Update README/CLAUDE.md

### Task List (Sequenced)

#### T001: Update PubMed Agent Tests (P0) - TDD Start
**Dependency**: None
**Description**: Modify existing PubMed agent tests to expect Czech input/output.
**Files**: `tests/unit_tests/nodes/test_pubmed_agent.py`
**Acceptance**:
- [ ] Tests use Czech queries (e.g., "studie o diabetu")
- [ ] Mock responses in Czech
- [ ] Test Czech response generation
- [ ] Tests FAIL initially (no implementation yet)

#### T002: Refactor PubMed Agent for Direct Czech (P0)
**Dependency**: T001 (tests exist)
**Description**: Update `pubmed_agent_node` to process Czech queries directly.
**Files**: `src/agent/nodes/pubmed_agent.py`
**Acceptance**:
- [ ] Remove `research_query` dependency
- [ ] Parse query from `state.messages[-1].content`
- [ ] Add Claude Sonnet 4.5 integration for Czech response
- [ ] Convert English abstracts to Czech inline
- [ ] Tests T001 PASS

#### T003: Update Integration Tests (P0)
**Dependency**: T002 (agent works)
**Description**: Update integration tests for simplified research flow.
**Files**: `tests/integration_tests/test_research_flow.py`
**Acceptance**:
- [ ] Remove translation steps from flow
- [ ] Test direct `route_query` → `pubmed_agent` → end
- [ ] Validate Czech responses
- [ ] Tests PASS

#### T004: Update Graph Definition (P0)
**Dependency**: T002, T003 (implementation + tests ready)
**Description**: Remove translation nodes and edges from graph.
**Files**: `src/agent/graph.py`
**Acceptance**:
- [ ] Remove `.add_node("translate_cz_to_en", ...)` and `translate_en_to_cz`
- [ ] Update conditional routing: `"translate_cz_to_en"` → `"pubmed_agent"`
- [ ] Remove translation edges
- [ ] Add direct `pubmed_agent → __end__` edge
- [ ] Graph compiles without errors
- [ ] LangGraph Studio visualizes correctly

#### T005: Update Routing Tests (P0)
**Dependency**: T004 (graph updated)
**Description**: Update routing tests for new edge mapping.
**Files**: `tests/unit_tests/test_routing.py`
**Acceptance**:
- [ ] Research keywords route to `"pubmed_agent"` (not translation)
- [ ] Drug keywords still route to `"drug_agent"`
- [ ] All routing tests PASS

#### T006: Remove State ResearchQuery Field (P1)
**Dependency**: T002, T004 (no code uses it)
**Description**: Delete `research_query` from State dataclass.
**Files**: `src/agent/graph.py`
**Acceptance**:
- [ ] Remove `research_query: ResearchQuery | None` line
- [ ] Type checking passes (`mypy --strict`)
- [ ] No broken references

#### T007: Delete Translation Files (P1)
**Dependency**: T004 (graph doesn't import them)
**Description**: Remove translation node files and tests.
**Files**:
- `src/agent/nodes/translation.py`
- `src/agent/utils/translation_prompts.py`
- `tests/unit_tests/nodes/test_translation.py`
**Acceptance**:
- [ ] Files deleted
- [ ] No import errors in codebase
- [ ] Test suite runs without errors

#### T008: Remove Anthropic API Dependency (P2)
**Dependency**: T007 (no code needs it)
**Description**: Comment out ANTHROPIC_API_KEY from .env.
**Files**: `.env`
**Acceptance**:
- [ ] `ANTHROPIC_API_KEY` line commented or removed
- [ ] PubMed agent still works (uses BioMCP only)
- [ ] README updated (key not required)

#### T009: Update CLAUDE.md Documentation (P2)
**Dependency**: T008 (all implementation complete)
**Description**: Remove Sandwich Pattern documentation, update architecture.
**Files**: `CLAUDE.md`
**Acceptance**:
- [ ] Remove Sandwich Pattern workflow description
- [ ] Update PubMed agent section (direct Czech)
- [ ] Update architecture diagram (if exists)
- [ ] Environment variables section updated

#### T010: Update README.md (P2)
**Dependency**: T009
**Description**: Update user-facing documentation.
**Files**: `README.md`
**Acceptance**:
- [ ] Quick Start: Remove ANTHROPIC_API_KEY requirement
- [ ] Feature 005 description updated
- [ ] Troubleshooting section updated
- [ ] Testing section updated (translation tests removed)

#### T011: Run Full Quality Checks (P0)
**Dependency**: T001-T010 (all tasks complete)
**Description**: Verify all quality gates pass.
**Commands**:
```bash
# Type checking
mypy --strict src/agent/nodes/pubmed_agent.py
mypy --strict src/agent/graph.py

# Linting
ruff format .
ruff check .

# Testing
PYTHONPATH=src uv run pytest tests/unit_tests/ -v
PYTHONPATH=src uv run pytest tests/integration_tests/ -v

# Coverage check
pytest --cov=src/agent --cov-report=term-missing
```
**Acceptance**:
- [ ] mypy: 0 errors
- [ ] ruff: All checks pass
- [ ] pytest: ≥169/175 tests passing
- [ ] coverage: ≥80%

#### T012: Manual Validation in LangGraph Studio (P0)
**Dependency**: T011 (quality checks pass)
**Description**: Visual validation of graph and end-to-end testing.
**Process**:
1. Start `langgraph dev`
2. Open LangGraph Studio
3. Verify graph visualization (no translation nodes)
4. Test Czech query: "jaké jsou studie o diabetu typu 2"
5. Verify response in Czech with citations
**Acceptance**:
- [ ] Graph shows simplified structure
- [ ] Czech queries return Czech responses
- [ ] Latency <5s
- [ ] Citations [1][2][3] work

---

## Risks & Mitigation

### Risk 1: Czech Response Quality Degradation
**Probability**: Medium
**Impact**: High
**Mitigation**:
- Compare old vs. new responses for 10 sample queries
- Manual review by Czech native speaker
- Fallback plan: Rollback to translation layer if quality unacceptable

**Contingency**: Keep translation code in git history for easy rollback.

### Risk 2: BioMCP Query Interpretation Issues
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Test BioMCP with Czech queries in sandbox
- Monitor search result quality
- Add query preprocessing if needed (keyword extraction)

**Contingency**: Add Czech→English query preprocessing layer if BioMCP struggles.

### Risk 3: Test Coverage Drop
**Probability**: Low
**Impact**: Medium
**Mitigation**:
- Track coverage before/after
- Ensure PubMed agent tests cover Czech scenarios
- Add integration tests for edge cases

**Monitoring**: Coverage report in CI/CD pipeline.

---

## Rollback Plan

### If Refactoring Fails

**Trigger Conditions:**
- Czech response quality unacceptable (user feedback)
- Integration tests fail consistently
- Performance regression >10% (latency increase)

**Rollback Steps:**
1. Revert commits (git history preserved)
2. Re-enable translation nodes in graph
3. Update routing to use translation path
4. Re-add ANTHROPIC_API_KEY to .env
5. Run tests to verify rollback successful

**Estimated Rollback Time**: <1 hour

### Partial Rollback

If only Czech quality is issue:
- Keep simplified graph
- Add optional translation preprocessing in PubMed agent
- Feature flag: `ENABLE_TRANSLATION=true/false` in .env

---

## Success Metrics

### Quantitative Metrics

1. **Latency Improvement**: Research queries respond in ≤5s (baseline: 8-10s)
   - Measurement: LangSmith trace duration
   - Target: 40-50% reduction

2. **Cost Reduction**: API usage reduced by 66%
   - Measurement: LangSmith API call count
   - Target: 3 calls → 1 call per research query

3. **Test Coverage**: Maintain ≥80% coverage
   - Measurement: pytest-cov report
   - Target: ≥169/175 tests passing

4. **Code Complexity**: Reduce graph nodes by 40%
   - Measurement: Node count in graph.py
   - Baseline: 5 nodes (research flow) → Target: 3 nodes

### Qualitative Metrics

1. **Czech Response Quality**: Responses are natural and accurate
   - Validation: Manual review by Czech doctors
   - Acceptance: 90% satisfaction rate

2. **Developer Experience**: Simpler debugging and maintenance
   - Validation: Team feedback
   - Metric: Reduced debugging time for research queries

3. **Graph Visualization**: Clearer flow in LangGraph Studio
   - Validation: Visual inspection
   - Metric: Easier to understand for new developers

---

## Timeline Estimate

### Sequenced Implementation

**Phase 1: Core Refactoring (2-3 hours)**
- T001: Update PubMed agent tests (30 min)
- T002: Refactor PubMed agent (60 min)
- T003: Update integration tests (30 min)
- T004: Update graph definition (30 min)
- T005: Update routing tests (15 min)

**Phase 2: Cleanup (1 hour)**
- T006: Remove ResearchQuery (15 min)
- T007: Delete translation files (15 min)
- T008: Remove ANTHROPIC_API_KEY (10 min)
- T009-T010: Update docs (20 min)

**Phase 3: Validation (1 hour)**
- T011: Quality checks (30 min)
- T012: Manual validation (30 min)

**Total Estimated Time**: 4-5 hours (single developer, focused work)

---

## Next Steps

1. **Review & Approve Plan**: Stakeholder sign-off
2. **Execute Tasks**: Follow sequence T001→T012
3. **Manual Validation**: LangGraph Studio testing
4. **User Acceptance**: Czech doctor feedback
5. **Deploy**: Merge to main after all gates pass

---

**Plan Status**: ✅ READY FOR IMPLEMENTATION
**Next Command**: `/speckit.tasks` - Generate detailed task breakdown
**Estimated Effort**: 4-5 hours
**Risk Level**: LOW (well-understood refactoring)
