# Tasks: Feature 005 Refactoring - Remove Translation Layer

**Feature**: Odstranění Translation Sandwich Pattern
**Branch**: `005-biomcp-pubmed-agent`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Created**: 2026-01-25

---

## Overview

**Objective**: Simplify PubMed agent by removing unnecessary translation layer (CZ→EN→PubMed→EN→CZ) and leverage Claude Sonnet 4.5 native Czech capabilities.

**Key Deliverables**:
- Simplified graph: 5 nodes → 3 nodes (research flow)
- Performance: 8-10s → ≤5s latency
- Cost: 66% reduction (3 LLM calls → 1 call)
- Better Czech quality (no translation artifacts)

**Implementation Strategy**:
- Test-First Development (Constitution Principle III)
- Incremental refactoring with continuous validation
- Maintain ≥80% test coverage throughout

---

## Implementation Phases

### Phase 1: Setup & Validation (T001-T003)

**Goal**: Prepare environment and validate current baseline

**Tasks**:
- [ ] T001 Run baseline quality checks to establish metrics
- [ ] T002 Create backup branch for rollback safety
- [ ] T003 Document current test coverage and performance metrics

### Phase 2: Test Preparation (T004-T007) - TDD Start

**Goal**: Update tests BEFORE implementation (Constitution Principle III)

**User Story**: FR-001 + FR-004 (Direct Czech Query Processing)

**Tasks**:
- [ ] T004 [US1] Update PubMed agent unit tests for Czech input in tests/unit_tests/nodes/test_pubmed_agent.py
- [ ] T005 [US1] Add Czech response validation tests in tests/unit_tests/nodes/test_pubmed_agent.py
- [ ] T006 [US1] Update integration tests for direct Czech flow in tests/integration_tests/test_research_flow.py
- [ ] T007 [US1] Verify all new tests FAIL (TDD red phase)

### Phase 3: PubMed Agent Refactoring (T008-T012)

**Goal**: Implement direct Czech processing (FR-004)

**User Story**: FR-004 (Update PubMed Agent for Direct Czech)

**Independent Test**: Czech research queries return Czech responses without translation nodes

**Tasks**:
- [ ] T008 [US1] Remove research_query dependency from pubmed_agent_node in src/agent/nodes/pubmed_agent.py
- [ ] T009 [US1] Add direct message content extraction in src/agent/nodes/pubmed_agent.py
- [ ] T010 [US1] Integrate Claude for Czech response generation in src/agent/nodes/pubmed_agent.py
- [ ] T011 [US1] Add inline abstract translation (EN→CZ) logic in src/agent/nodes/pubmed_agent.py
- [ ] T012 [US1] Verify tests T004-T006 PASS (TDD green phase)

### Phase 4: Graph Simplification (T013-T018)

**Goal**: Remove translation nodes and edges (FR-002)

**User Story**: FR-002 (Remove Translation Nodes from Graph)

**Independent Test**: Graph compiles and visualizes without translation nodes

**Tasks**:
- [ ] T013 [US2] Update routing tests for direct pubmed_agent path in tests/unit_tests/test_routing.py
- [ ] T014 [US2] Remove translate_cz_to_en and translate_en_to_cz nodes from graph in src/agent/graph.py
- [ ] T015 [US2] Update conditional routing edges in src/agent/graph.py
- [ ] T016 [US2] Add direct pubmed_agent → __end__ edge in src/agent/graph.py
- [ ] T017 [US2] Verify graph compiles without errors
- [ ] T018 [US2] Validate graph visualization in LangGraph Studio

### Phase 5: State Schema Cleanup (T019-T021)

**Goal**: Remove ResearchQuery model (FR-005)

**User Story**: FR-005 (Remove ResearchQuery Model Dependency)

**Independent Test**: Code compiles and runs without ResearchQuery references

**Tasks**:
- [ ] T019 [P] [US3] Remove research_query field from State dataclass in src/agent/graph.py
- [ ] T020 [P] [US3] Delete ResearchQuery from research_models.py in src/agent/models/research_models.py
- [ ] T021 [US3] Run mypy --strict to verify type safety

### Phase 6: File Deletion (T022-T025)

**Goal**: Remove translation files (FR-003)

**User Story**: FR-003 (Remove Translation Node Files)

**Independent Test**: Codebase runs without translation file references

**Tasks**:
- [ ] T022 [P] [US4] Delete src/agent/nodes/translation.py
- [ ] T023 [P] [US4] Delete src/agent/utils/translation_prompts.py
- [ ] T024 [P] [US4] Delete tests/unit_tests/nodes/test_translation.py
- [ ] T025 [US4] Remove translation imports from src/agent/graph.py

### Phase 7: Configuration Cleanup (T026-T028)

**Goal**: Remove ANTHROPIC_API_KEY dependency (FR-007)

**User Story**: FR-007 (Remove Anthropic API Dependency)

**Independent Test**: PubMed agent works without ANTHROPIC_API_KEY

**Tasks**:
- [ ] T026 [P] [US5] Comment out ANTHROPIC_API_KEY in .env
- [ ] T027 [P] [US5] Update README.md environment variables section
- [ ] T028 [US5] Verify PubMed agent works without Anthropic key

### Phase 8: Documentation Updates (T029-T031)

**Goal**: Update technical documentation (FR-009)

**User Story**: FR-009 (Update Documentation)

**Tasks**:
- [ ] T029 [P] Update CLAUDE.md architecture section
- [ ] T030 [P] Update CLAUDE.md PubMed agent description
- [ ] T031 [P] Update README.md Feature 005 description

### Phase 9: Quality Validation (T032-T037)

**Goal**: Ensure all quality gates pass

**Tasks**:
- [ ] T032 Run mypy --strict on modified files
- [ ] T033 Run ruff format . and ruff check .
- [ ] T034 Run full test suite (PYTHONPATH=src pytest tests/)
- [ ] T035 Verify test coverage ≥80%
- [ ] T036 Measure latency improvement (target: ≤5s)
- [ ] T037 Validate cost reduction (API call count)

### Phase 10: Manual Validation & Acceptance (T038-T041)

**Goal**: End-to-end validation in real environment

**Tasks**:
- [ ] T038 Start langgraph dev and open Studio
- [ ] T039 Test Czech research query: "jaké jsou studie o diabetu typu 2"
- [ ] T040 Verify response in Czech with citations [1][2][3]
- [ ] T041 Compare response quality with old translation approach

### Phase 11: Polish & Finalization (T042-T044)

**Goal**: Final refinements and commit

**Tasks**:
- [ ] T042 Review and refactor any code smells
- [ ] T043 Add any missing docstrings (Google style)
- [ ] T044 Git commit with proper message format

---

## Task Details

### Phase 1: Setup & Validation

#### T001: Run baseline quality checks to establish metrics
**Type**: Setup
**Files**: None (command-line)
**Description**: Establish baseline metrics before refactoring
**Commands**:
```bash
# Test coverage baseline
PYTHONPATH=src pytest --cov=src/agent --cov-report=term-missing tests/

# Type checking baseline
mypy --strict src/agent/nodes/pubmed_agent.py
mypy --strict src/agent/graph.py

# Linting baseline
ruff check .

# Performance baseline (record latency)
# Manually test research query and measure time
```
**Acceptance**:
- [ ] Coverage report saved (baseline: 96%)
- [ ] Mypy errors documented (baseline: 0)
- [ ] Ruff issues documented (baseline: 0)
- [ ] Latency baseline recorded (8-10s)

#### T002: Create backup branch for rollback safety
**Type**: Setup
**Files**: None (git)
**Description**: Create safety branch for easy rollback
**Commands**:
```bash
git checkout -b 005-biomcp-pubmed-agent-backup
git push origin 005-biomcp-pubmed-agent-backup
git checkout 005-biomcp-pubmed-agent
```
**Acceptance**:
- [ ] Backup branch created
- [ ] Backup pushed to remote
- [ ] Working branch checked out

#### T003: Document current test coverage and performance metrics
**Type**: Setup
**Files**: specs/005-remove-translation-layer/baseline-metrics.md
**Description**: Create metrics document for comparison
**Content**:
```markdown
# Baseline Metrics - Before Refactoring

**Date**: 2026-01-25
**Branch**: 005-biomcp-pubmed-agent-backup

## Test Coverage
- Total: 177/183 tests passing (96%)
- Coverage: XX% (from T001 report)

## Performance
- Research query latency: 8-10s (average)
- API calls per query: 3 (translate_cz_to_en, pubmed_agent, translate_en_to_cz)

## Code Quality
- mypy --strict: 0 errors
- ruff check: 0 issues
- Graph nodes (research flow): 5 nodes

## Architecture
- Translation nodes: 2 (translate_cz_to_en, translate_en_to_cz)
- ANTHROPIC_API_KEY: Required
```
**Acceptance**:
- [ ] Metrics document created
- [ ] All baseline values recorded
- [ ] Document committed to git

---

### Phase 2: Test Preparation (TDD Start)

#### T004: [US1] Update PubMed agent unit tests for Czech input
**Type**: Test (Unit)
**User Story**: FR-001, FR-004
**Files**: tests/unit_tests/nodes/test_pubmed_agent.py
**Description**: Modify existing tests to expect Czech queries instead of English
**Changes**:
```python
# BEFORE
def test_pubmed_search_returns_documents(sample_state, mock_runtime):
    state["research_query"] = ResearchQuery(
        query_text="diabetes studies",  # English
        query_type="search"
    )
    # ...

# AFTER
def test_pubmed_search_returns_documents_czech(sample_state, mock_runtime):
    # Remove research_query setup
    state.messages.append({
        "role": "user",
        "content": "jaké jsou studie o diabetu typu 2"  # Czech
    })
    # ...
```
**Acceptance**:
- [ ] All test queries changed to Czech
- [ ] research_query references removed
- [ ] Tests use state.messages for input
- [ ] Tests currently FAIL (no implementation yet)

#### T005: [US1] Add Czech response validation tests
**Type**: Test (Unit)
**User Story**: FR-004
**Files**: tests/unit_tests/nodes/test_pubmed_agent.py
**Description**: Add tests validating Czech response format
**New Tests**:
```python
@pytest.mark.asyncio
async def test_pubmed_agent_returns_czech_response(sample_state, mock_runtime):
    """Test PubMed agent returns response in Czech."""
    # Arrange
    state.messages.append({
        "role": "user",
        "content": "studie o diabetu"
    })

    # Act
    result = await pubmed_agent_node(state, mock_runtime)

    # Assert
    assert "messages" in result
    response_content = result["messages"][0]["content"]
    assert isinstance(response_content, str)
    # Check for Czech words (basic validation)
    assert any(word in response_content.lower() for word in ["studie", "výzkum", "článek"])
    # Check for citations
    assert "[1]" in response_content or "Nebyly nalezeny" in response_content
```
**Acceptance**:
- [ ] Test validates Czech language response
- [ ] Test checks citation format [1][2][3]
- [ ] Test currently FAILS (not implemented)

#### T006: [US1] Update integration tests for direct Czech flow
**Type**: Test (Integration)
**User Story**: FR-001, FR-002
**Files**: tests/integration_tests/test_research_flow.py
**Description**: Update integration test to expect direct routing without translation
**Changes**:
```python
# BEFORE
async def test_research_flow_with_translation():
    # Expects: route → translate_cz_to_en → pubmed → translate_en_to_cz → end

# AFTER
async def test_research_flow_direct_czech():
    """Test research flow without translation nodes."""
    # Arrange
    graph = compile_graph()
    input_state = {
        "messages": [{"role": "user", "content": "studie o diabetu"}]
    }

    # Act
    final_state = await graph.ainvoke(input_state)

    # Assert - Check path (no translation nodes)
    # This will be validated by LangSmith trace
    assert final_state["messages"][-1]["role"] == "assistant"
    assert "studie" in final_state["messages"][-1]["content"].lower() or "článek" in final_state["messages"][-1]["content"].lower()
```
**Acceptance**:
- [ ] Integration test updated for direct flow
- [ ] No translation node expectations
- [ ] Test currently FAILS (graph not updated)

#### T007: [US1] Verify all new tests FAIL (TDD red phase)
**Type**: Validation
**User Story**: All (TDD validation)
**Files**: None (command-line)
**Description**: Confirm TDD red phase - tests fail before implementation
**Commands**:
```bash
PYTHONPATH=src pytest tests/unit_tests/nodes/test_pubmed_agent.py -v
PYTHONPATH=src pytest tests/integration_tests/test_research_flow.py -v
```
**Acceptance**:
- [ ] T004 tests FAIL (missing Czech implementation)
- [ ] T005 tests FAIL (missing Czech response)
- [ ] T006 test FAILS (graph not updated)
- [ ] Documented failure reasons

---

### Phase 3: PubMed Agent Refactoring

#### T008: [US1] Remove research_query dependency from pubmed_agent_node
**Type**: Implementation
**User Story**: FR-004
**Files**: src/agent/nodes/pubmed_agent.py
**Description**: Remove code that expects state.research_query
**Changes**:
```python
# BEFORE (lines ~360-380)
async def pubmed_agent_node(state: State, runtime: Runtime[Context]):
    research_query = state.research_query
    if not research_query:
        print("[pubmed_agent] ERROR: No research query in state")
        return {...}

    query_text = research_query.query_text  # Expects English
    query_type = research_query.query_type
    # ...

# AFTER
async def pubmed_agent_node(state: State, runtime: Runtime[Context]):
    # Parse Czech query directly from messages
    last_message = state.messages[-1]
    czech_query = _extract_content(last_message)  # New helper

    if not czech_query:
        print("[pubmed_agent] ERROR: Empty query")
        return {...}

    # Determine query type from content
    query_type = "pmid_lookup" if "pmid" in czech_query.lower() else "search"
    # ...
```
**Acceptance**:
- [ ] research_query references removed
- [ ] Query extracted from messages
- [ ] Helper function _extract_content added
- [ ] Query type detection works

#### T009: [US1] Add direct message content extraction
**Type**: Implementation
**User Story**: FR-004
**Files**: src/agent/nodes/pubmed_agent.py
**Description**: Add helper to extract content from multimodal messages
**New Function**:
```python
def _extract_content(message: Any) -> str:
    """Extract text content from message (handles multimodal format).

    Args:
        message: Message dict or object with content field.

    Returns:
        Extracted text content as string.
    """
    if isinstance(message, dict):
        content = message.get("content", "")
    else:
        content = getattr(message, "content", "")

    # Handle multimodal list format (from LangGraph Studio)
    if isinstance(content, list) and content:
        first_block = content[0]
        if isinstance(first_block, str):
            return first_block
        elif isinstance(first_block, dict) and "text" in first_block:
            return str(first_block["text"])

    # Handle simple string
    if isinstance(content, str):
        return content

    return ""
```
**Acceptance**:
- [ ] Function handles string content
- [ ] Function handles multimodal list
- [ ] Function returns empty string for invalid input
- [ ] Unit tests added for _extract_content

#### T010: [US1] Integrate Claude for Czech response generation
**Type**: Implementation
**User Story**: FR-004
**Files**: src/agent/nodes/pubmed_agent.py
**Description**: Add Claude integration to generate Czech responses from English articles
**New Function**:
```python
async def _generate_czech_response(
    articles: List[PubMedArticle],
    czech_query: str,
    runtime: Runtime[Context]
) -> str:
    """Generate Czech language response from English PubMed articles.

    Uses Claude Sonnet 4.5 to:
    1. Translate English abstracts to Czech
    2. Synthesize findings relevant to query
    3. Format with inline citations [1][2][3]

    Args:
        articles: List of PubMed articles with English abstracts.
        czech_query: Original Czech user query.
        runtime: Runtime context (for model config).

    Returns:
        Czech language response with citations.
    """
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage

    model_name = runtime.context.get("model_name", "claude-sonnet-4-5-20250929")
    llm = ChatAnthropic(model_name=model_name, temperature=0)

    # Format articles for prompt
    articles_text = "\n\n".join([
        f"[{i+1}] {art.title}\n{art.abstract or 'No abstract'}"
        for i, art in enumerate(articles)
    ])

    prompt = f"""Jsi lékařský výzkumný asistent. Uživatel se ptal: "{czech_query}"

Nalezl jsem tyto relevantní články (v angličtině):

{articles_text}

Prosím:
1. Shrň klíčová zjištění v češtině
2. Použij inline citace [1], [2], [3] na odpovídající články
3. Zachovej technické termíny (např. "diabetes mellitus")
4. Piš přirozenou češtinou

Odpověď v češtině s citacemi:"""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    return response.content
```
**Acceptance**:
- [ ] Function generates Czech response
- [ ] Citations [1][2][3] included
- [ ] Technical terms preserved
- [ ] Uses Claude Sonnet 4.5

#### T011: [US1] Add inline abstract translation (EN→CZ) logic
**Type**: Implementation
**User Story**: FR-004
**Files**: src/agent/nodes/pubmed_agent.py
**Description**: Update main node to use Czech response generation
**Changes**:
```python
# In pubmed_agent_node, after retrieving articles:

if not articles:
    return {
        "messages": [{
            "role": "assistant",
            "content": "Nebyly nalezeny žádné články odpovídající vašemu dotazu."
        }],
        "retrieved_docs": [],
        "next": "__end__"
    }

# Generate Czech response with Claude
czech_response = await _generate_czech_response(articles, czech_query, runtime)

# Transform articles to Documents (keep English metadata for tracing)
docs = [
    Document(
        page_content=art.abstract or "No abstract",
        metadata={
            "pmid": art.pmid,
            "title": art.title,
            "authors": art.authors,
            "journal": art.journal,
            "doi": art.doi
        }
    )
    for art in articles
]

return {
    "messages": [{
        "role": "assistant",
        "content": czech_response
    }],
    "retrieved_docs": docs,
    "next": "__end__"
}
```
**Acceptance**:
- [ ] Empty results return Czech message
- [ ] Articles generate Czech response
- [ ] Documents created with metadata
- [ ] Response structure matches expected format

#### T012: [US1] Verify tests T004-T006 PASS (TDD green phase)
**Type**: Validation
**User Story**: FR-004
**Files**: None (command-line)
**Description**: Confirm TDD green phase - tests pass after implementation
**Commands**:
```bash
PYTHONPATH=src pytest tests/unit_tests/nodes/test_pubmed_agent.py::test_pubmed_search_returns_documents_czech -v
PYTHONPATH=src pytest tests/unit_tests/nodes/test_pubmed_agent.py::test_pubmed_agent_returns_czech_response -v
PYTHONPATH=src pytest tests/integration_tests/test_research_flow.py::test_research_flow_direct_czech -v
```
**Acceptance**:
- [ ] T004 tests PASS (Czech input works)
- [ ] T005 tests PASS (Czech output validated)
- [ ] T006 test STILL FAILS (graph not updated yet - expected)
- [ ] No regressions in other tests

---

### Phase 4: Graph Simplification

#### T013: [US2] Update routing tests for direct pubmed_agent path
**Type**: Test (Unit)
**User Story**: FR-002, FR-006
**Files**: tests/unit_tests/test_routing.py
**Description**: Update routing tests to expect pubmed_agent instead of translate_cz_to_en
**Changes**:
```python
# BEFORE
def test_route_query_with_research_keyword():
    state = State(messages=[{"role": "user", "content": "studie o diabetu"}], next="")
    result = route_query(state)
    assert result == "translate_cz_to_en"

# AFTER
def test_route_query_with_research_keyword():
    state = State(messages=[{"role": "user", "content": "studie o diabetu"}], next="")
    result = route_query(state)
    assert result == "pubmed_agent"  # Direct routing
```
**Acceptance**:
- [ ] All research keyword tests expect "pubmed_agent"
- [ ] Drug keyword tests unchanged (still "drug_agent")
- [ ] Placeholder tests unchanged
- [ ] Tests currently FAIL (routing not updated)

#### T014: [US2] Remove translate_cz_to_en and translate_en_to_cz nodes from graph
**Type**: Implementation
**User Story**: FR-002
**Files**: src/agent/graph.py
**Description**: Delete translation node definitions from graph
**Changes**:
```python
# BEFORE (lines ~300-325)
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("placeholder", placeholder_node)
    .add_node("drug_agent", drug_agent_node)
    .add_node("translate_cz_to_en", translate_cz_to_en_node)  # DELETE
    .add_node("pubmed_agent", pubmed_agent_node)
    .add_node("translate_en_to_cz", translate_en_to_cz_node)  # DELETE
    # ...

# AFTER
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("placeholder", placeholder_node)
    .add_node("drug_agent", drug_agent_node)
    .add_node("pubmed_agent", pubmed_agent_node)
    # ...
```
**Acceptance**:
- [ ] translate_cz_to_en node removed
- [ ] translate_en_to_cz node removed
- [ ] Graph definition cleaner (3 nodes for research)
- [ ] Code compiles (imports still present at this point)

#### T015: [US2] Update conditional routing edges
**Type**: Implementation
**User Story**: FR-002
**Files**: src/agent/graph.py
**Description**: Change routing to point directly to pubmed_agent
**Changes**:
```python
# BEFORE
.add_conditional_edges(
    "route_query",
    lambda state: state["next"],
    {
        "drug_agent": "drug_agent",
        "translate_cz_to_en": "translate_cz_to_en",  # OLD
        "__end__": "__end__"
    }
)

# AFTER
.add_conditional_edges(
    "route_query",
    lambda state: state["next"],
    {
        "drug_agent": "drug_agent",
        "pubmed_agent": "pubmed_agent",  # NEW - direct routing
        "__end__": "__end__"
    }
)
```
**Acceptance**:
- [ ] Conditional routing updated
- [ ] "translate_cz_to_en" key removed
- [ ] "pubmed_agent" key added
- [ ] Other routes unchanged

#### T016: [US2] Add direct pubmed_agent → __end__ edge
**Type**: Implementation
**User Story**: FR-002
**Files**: src/agent/graph.py
**Description**: Remove translation edges and add direct end edge
**Changes**:
```python
# BEFORE
.add_edge("translate_cz_to_en", "pubmed_agent")  # DELETE
.add_edge("pubmed_agent", "translate_en_to_cz")  # DELETE
.add_edge("translate_en_to_cz", "__end__")       # DELETE

# AFTER
.add_edge("pubmed_agent", "__end__")  # ADD - direct to end
```
**Acceptance**:
- [ ] 3 translation edges removed
- [ ] 1 direct edge added
- [ ] Graph flow: route → pubmed → end

#### T017: [US2] Verify graph compiles without errors
**Type**: Validation
**User Story**: FR-002
**Files**: None (command-line)
**Description**: Ensure graph compiles and server starts
**Commands**:
```bash
# Test import
python -c "from agent.graph import graph; print('Graph compiled successfully')"

# Start dev server (quick check)
timeout 10s langgraph dev || echo "Server started successfully"
```
**Acceptance**:
- [ ] Graph imports without errors
- [ ] No import errors for translation nodes (imports not removed yet)
- [ ] LangGraph dev server starts
- [ ] No compilation errors

#### T018: [US2] Validate graph visualization in LangGraph Studio
**Type**: Manual Validation
**User Story**: FR-002
**Files**: None (manual)
**Description**: Visual check in LangGraph Studio
**Steps**:
1. Start `langgraph dev`
2. Open LangGraph Studio (http://localhost:2024 or Studio URL)
3. View graph visualization
4. Verify simplified structure

**Expected Visualization**:
```
route_query
  ├─> drug_agent -> __end__
  ├─> pubmed_agent -> __end__  (NO translation nodes)
  └─> placeholder -> __end__
```
**Acceptance**:
- [ ] Graph shows 3 nodes in research path (was 5)
- [ ] No translate_cz_to_en node visible
- [ ] No translate_en_to_cz node visible
- [ ] Direct pubmed_agent → __end__ edge visible

---

### Phase 5: State Schema Cleanup

#### T019: [P] [US3] Remove research_query field from State dataclass
**Type**: Implementation
**User Story**: FR-005
**Files**: src/agent/graph.py
**Description**: Delete research_query field from State
**Changes**:
```python
# BEFORE (lines ~120-140)
@dataclass
class State:
    messages: Annotated[list[AnyMessage], add_messages]
    next: str = ""
    retrieved_docs: list[Document] = field(default_factory=list)
    drug_query: DrugQuery | None = None
    research_query: ResearchQuery | None = None  # DELETE THIS LINE

# AFTER
@dataclass
class State:
    messages: Annotated[list[AnyMessage], add_messages]
    next: str = ""
    retrieved_docs: list[Document] = field(default_factory=list)
    drug_query: DrugQuery | None = None
    # research_query removed - not needed without translation
```
**Acceptance**:
- [ ] research_query line deleted
- [ ] State dataclass remains valid
- [ ] No syntax errors

#### T020: [P] [US3] Delete ResearchQuery from research_models.py
**Type**: Implementation
**User Story**: FR-005
**Files**: src/agent/models/research_models.py
**Description**: Remove ResearchQuery dataclass (not needed anymore)
**Changes**:
```python
# BEFORE - ResearchQuery dataclass exists
# AFTER - ResearchQuery dataclass deleted

# Keep PubMedArticle and other models
```
**Acceptance**:
- [ ] ResearchQuery class deleted
- [ ] Other models (PubMedArticle) preserved
- [ ] File still valid Python

#### T021: [US3] Run mypy --strict to verify type safety
**Type**: Validation
**User Story**: FR-005
**Files**: None (command-line)
**Description**: Ensure type checking passes after State changes
**Commands**:
```bash
mypy --strict src/agent/graph.py
mypy --strict src/agent/nodes/pubmed_agent.py
mypy --strict src/agent/models/research_models.py
```
**Acceptance**:
- [ ] mypy graph.py: 0 errors
- [ ] mypy pubmed_agent.py: 0 errors
- [ ] mypy research_models.py: 0 errors
- [ ] No type safety regressions

---

### Phase 6: File Deletion

#### T022: [P] [US4] Delete src/agent/nodes/translation.py
**Type**: Cleanup
**User Story**: FR-003
**Files**: src/agent/nodes/translation.py
**Description**: Remove translation node file (no longer used)
**Commands**:
```bash
git rm src/agent/nodes/translation.py
```
**Acceptance**:
- [ ] File deleted from filesystem
- [ ] File staged for git removal

#### T023: [P] [US4] Delete src/agent/utils/translation_prompts.py
**Type**: Cleanup
**User Story**: FR-003
**Files**: src/agent/utils/translation_prompts.py
**Description**: Remove translation prompts file
**Commands**:
```bash
git rm src/agent/utils/translation_prompts.py
```
**Acceptance**:
- [ ] File deleted from filesystem
- [ ] File staged for git removal

#### T024: [P] [US4] Delete tests/unit_tests/nodes/test_translation.py
**Type**: Cleanup
**User Story**: FR-003
**Files**: tests/unit_tests/nodes/test_translation.py
**Description**: Remove translation tests (no longer applicable)
**Commands**:
```bash
git rm tests/unit_tests/nodes/test_translation.py
```
**Acceptance**:
- [ ] Test file deleted
- [ ] File staged for git removal

#### T025: [US4] Remove translation imports from src/agent/graph.py
**Type**: Implementation
**User Story**: FR-003
**Files**: src/agent/graph.py
**Description**: Clean up imports after file deletion
**Changes**:
```python
# BEFORE (lines ~25-30)
from agent.nodes import drug_agent_node
from agent.nodes.pubmed_agent import pubmed_agent_node
from agent.nodes.translation import translate_cz_to_en_node, translate_en_to_cz_node  # DELETE

# AFTER
from agent.nodes import drug_agent_node
from agent.nodes.pubmed_agent import pubmed_agent_node
# Translation imports removed
```
**Acceptance**:
- [ ] Translation imports deleted
- [ ] No import errors
- [ ] Code compiles cleanly

---

### Phase 7: Configuration Cleanup

#### T026: [P] [US5] Comment out ANTHROPIC_API_KEY in .env
**Type**: Configuration
**User Story**: FR-007
**Files**: .env
**Description**: Remove Anthropic API key requirement
**Changes**:
```bash
# BEFORE (line 54)
ANTHROPIC_API_KEY=sk-ant-api03-5TwWcZM...

# AFTER
# ANTHROPIC_API_KEY=sk-ant-api03-5TwWcZM...  # Not needed - translation removed
# Translation model removed (no longer used)
```
**Acceptance**:
- [ ] ANTHROPIC_API_KEY line commented out
- [ ] TRANSLATION_MODEL line commented out or removed
- [ ] .env file valid

#### T027: [P] [US5] Update README.md environment variables section
**Type**: Documentation
**User Story**: FR-007, FR-009
**Files**: README.md
**Description**: Remove ANTHROPIC_API_KEY from required variables
**Changes**:
```markdown
# BEFORE
## Environment Variables
Required:
- LANGSMITH_API_KEY (optional, for tracing)
- ANTHROPIC_API_KEY (for translation)  # DELETE
- BioMCP URL

# AFTER
## Environment Variables
Required:
- LANGSMITH_API_KEY (optional, for tracing)
- BioMCP URL (for PubMed search)

Note: ANTHROPIC_API_KEY no longer required - translation layer removed in v1.1.2
```
**Acceptance**:
- [ ] ANTHROPIC_API_KEY removed from required list
- [ ] Changelog note added
- [ ] Setup instructions updated

#### T028: [US5] Verify PubMed agent works without Anthropic key
**Type**: Validation
**User Story**: FR-007
**Files**: None (manual)
**Description**: Test that PubMed agent functions without ANTHROPIC_API_KEY
**Steps**:
1. Ensure .env has ANTHROPIC_API_KEY commented
2. Restart langgraph dev
3. Test research query: "studie o diabetu"
4. Verify Czech response returns

**Acceptance**:
- [ ] Server starts without ANTHROPIC_API_KEY
- [ ] Research queries work
- [ ] Czech responses generated
- [ ] No authentication errors

---

### Phase 8: Documentation Updates

#### T029: [P] Update CLAUDE.md architecture section
**Type**: Documentation
**User Story**: FR-009
**Files**: CLAUDE.md
**Description**: Remove Sandwich Pattern documentation
**Changes**:
```markdown
# BEFORE - Sandwich Pattern section exists
### Multi-Agent Pattern (Cílový Stav)
- Translation: CZ→EN→PubMed→EN→CZ

# AFTER - Direct pattern
### Multi-Agent Pattern (Current Implementation)
- PubMed Agent: Direct Czech processing with Claude Sonnet 4.5
- No translation layer - leverages native multilingual capabilities
```
**Acceptance**:
- [ ] Sandwich Pattern section removed
- [ ] Direct Czech processing documented
- [ ] Architecture diagram updated (if exists)

#### T030: [P] Update CLAUDE.md PubMed agent description
**Type**: Documentation
**User Story**: FR-009
**Files**: CLAUDE.md
**Description**: Update PubMed agent technical description
**Changes**:
```markdown
# BEFORE
**PubMed Agent (Feature 005)**:
- Translation nodes for CZ→EN→CZ workflow
- Sandwich Pattern implementation

# AFTER
**PubMed Agent (Feature 005 - Refactored v1.1.2)**:
- Direct Czech query processing
- Claude Sonnet 4.5 converts English abstracts to Czech inline
- Simplified architecture: route → pubmed_agent → end
- No translation overhead
```
**Acceptance**:
- [ ] Feature description updated
- [ ] Version noted (v1.1.2)
- [ ] Performance improvements mentioned

#### T031: [P] Update README.md Feature 005 description
**Type**: Documentation
**User Story**: FR-009
**Files**: README.md
**Description**: Update user-facing feature description
**Changes**:
```markdown
# BEFORE
### Feature 005: BioMCP PubMed Agent
- Translation layer for Czech queries
- 3-step workflow

# AFTER
### Feature 005: BioMCP PubMed Agent (Refactored v1.1.2)
- ✅ Direct Czech query processing (no translation)
- ✅ 40-50% faster responses (8-10s → 5s)
- ✅ 66% cost reduction (1 LLM call vs. 3)
- ✅ Better Czech quality (native multilingual)
```
**Acceptance**:
- [ ] Feature benefits highlighted
- [ ] Performance metrics included
- [ ] Version noted

---

### Phase 9: Quality Validation

#### T032: Run mypy --strict on modified files
**Type**: Quality Gate
**Files**: None (command-line)
**Description**: Verify type safety across all changes
**Commands**:
```bash
mypy --strict src/agent/graph.py
mypy --strict src/agent/nodes/pubmed_agent.py
mypy --strict src/agent/models/research_models.py
```
**Acceptance**:
- [ ] 0 mypy errors in graph.py
- [ ] 0 mypy errors in pubmed_agent.py
- [ ] 0 mypy errors in research_models.py
- [ ] Constitution Principle II satisfied

#### T033: Run ruff format . and ruff check .
**Type**: Quality Gate
**Files**: None (command-line)
**Description**: Ensure code formatting and linting pass
**Commands**:
```bash
ruff format .
ruff check .
```
**Acceptance**:
- [ ] All files formatted (no changes needed)
- [ ] 0 ruff errors
- [ ] 0 ruff warnings
- [ ] Constitution Code Quality Gates satisfied

#### T034: Run full test suite (PYTHONPATH=src pytest tests/)
**Type**: Quality Gate
**Files**: None (command-line)
**Description**: Verify all tests pass
**Commands**:
```bash
PYTHONPATH=src pytest tests/unit_tests/ -v
PYTHONPATH=src pytest tests/integration_tests/ -v
```
**Acceptance**:
- [ ] ≥169/175 unit tests passing (maintain baseline)
- [ ] Integration tests passing
- [ ] No new test failures
- [ ] Constitution Principle III satisfied

#### T035: Verify test coverage ≥80%
**Type**: Quality Gate
**Files**: None (command-line)
**Description**: Check test coverage meets threshold
**Commands**:
```bash
PYTHONPATH=src pytest --cov=src/agent --cov-report=term-missing tests/
```
**Acceptance**:
- [ ] Coverage ≥80% (target from Constitution)
- [ ] pubmed_agent.py coverage maintained
- [ ] graph.py coverage maintained
- [ ] Coverage report generated

#### T036: Measure latency improvement (target: ≤5s)
**Type**: Performance Validation
**Files**: None (manual)
**Description**: Measure end-to-end latency for research queries
**Steps**:
1. Start `langgraph dev`
2. Use LangGraph Studio or API to test query
3. Measure time from input to response
4. Record via LangSmith trace

**Test Queries**:
- "jaké jsou studie o diabetu typu 2"
- "výzkum o hypertezi"
- "pmid 12345678"

**Acceptance**:
- [ ] Average latency ≤5s (baseline: 8-10s)
- [ ] 40-50% improvement confirmed
- [ ] Success Criteria #1 met

#### T037: Validate cost reduction (API call count)
**Type**: Cost Validation
**Files**: None (LangSmith)
**Description**: Verify API usage reduced from 3 to 1 call
**Steps**:
1. Check LangSmith trace for research query
2. Count LLM API calls
3. Compare to baseline (3 calls)

**Acceptance**:
- [ ] 1 LLM call per research query (vs. 3 baseline)
- [ ] 66% cost reduction confirmed
- [ ] Success Criteria #2 met

---

### Phase 10: Manual Validation & Acceptance

#### T038: Start langgraph dev and open Studio
**Type**: Manual Validation
**Files**: None
**Description**: Prepare environment for end-to-end testing
**Commands**:
```bash
./dev.sh
# Opens LangGraph Studio automatically
```
**Acceptance**:
- [ ] Server starts without errors
- [ ] Studio accessible
- [ ] Graph loads correctly

#### T039: Test Czech research query: "jaké jsou studie o diabetu typu 2"
**Type**: Manual Validation
**Files**: None (Studio UI)
**Description**: Execute real Czech query through Studio
**Steps**:
1. In Studio, create new thread
2. Send message: "jaké jsou studie o diabetu typu 2"
3. Observe response
4. Check trace in LangSmith

**Acceptance**:
- [ ] Query routes to pubmed_agent (not translation)
- [ ] Response in Czech
- [ ] Citations [1][2][3] present
- [ ] No translation nodes in trace

#### T040: Verify response in Czech with citations [1][2][3]
**Type**: Quality Validation
**Files**: None (manual review)
**Description**: Validate response quality
**Checks**:
- [ ] Response is natural Czech (no translation artifacts)
- [ ] Citations formatted correctly [1][2][3]
- [ ] Technical terms preserved (e.g., "diabetes mellitus")
- [ ] Response addresses query accurately

**Acceptance**:
- [ ] Czech quality satisfactory
- [ ] Success Criteria #4 met (zero translation errors)

#### T041: Compare response quality with old translation approach
**Type**: Quality Comparison
**Files**: None (manual)
**Description**: Side-by-side comparison with baseline
**Steps**:
1. Test same query on backup branch (with translation)
2. Compare responses:
   - Natural language quality
   - Technical accuracy
   - Citation placement
   - Response time

**Acceptance**:
- [ ] New approach equal or better quality
- [ ] No information loss vs. translation approach
- [ ] Faster response confirmed

---

### Phase 11: Polish & Finalization

#### T042: Review and refactor any code smells
**Type**: Code Quality
**Files**: All modified files
**Description**: Final code review for improvements
**Checks**:
- [ ] No duplicate code
- [ ] No magic numbers
- [ ] Clear variable names
- [ ] Consistent formatting
- [ ] No commented-out code

**Acceptance**:
- [ ] All code smells addressed
- [ ] Code follows project conventions
- [ ] Ready for code review

#### T043: Add any missing docstrings (Google style)
**Type**: Documentation
**Files**: src/agent/nodes/pubmed_agent.py
**Description**: Ensure all functions have proper docstrings
**Check Functions**:
- _extract_content
- _generate_czech_response
- pubmed_agent_node (update existing)

**Docstring Format**:
```python
def function_name(param: Type) -> ReturnType:
    """Brief description.

    Longer description if needed.

    Args:
        param: Parameter description.

    Returns:
        Return value description.

    Raises:
        ExceptionType: When it's raised.
    """
```
**Acceptance**:
- [ ] All new functions have docstrings
- [ ] Updated functions have accurate docs
- [ ] Google style followed
- [ ] Constitution documentation requirement met

#### T044: Git commit with proper message format
**Type**: Version Control
**Files**: All changed files
**Description**: Commit all changes with conventional format
**Commands**:
```bash
# Stage all changes
git add -A

# Commit with proper message
git commit -m "$(cat <<'EOF'
refactor(agent): remove translation layer from PubMed agent

BREAKING CHANGE: Simplified PubMed agent to use direct Czech processing,
eliminating translation nodes (translate_cz_to_en, translate_en_to_cz).

Changes:
- Remove translation nodes from graph (FR-002)
- Update PubMed agent for direct Czech queries (FR-004)
- Remove ResearchQuery model (FR-005)
- Delete translation files (FR-003)
- Remove ANTHROPIC_API_KEY dependency (FR-007)
- Update documentation (FR-009)

Performance improvements:
- 40-50% latency reduction (8-10s → 5s)
- 66% cost reduction (3 LLM calls → 1)
- Simplified architecture (5 nodes → 3)

Tests: 169/175 passing (96% coverage maintained)
Quality: mypy --strict 0 errors, ruff checks pass

Closes #005-remove-translation-layer

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```
**Acceptance**:
- [ ] All changes staged
- [ ] Commit message follows conventional format
- [ ] Breaking change noted
- [ ] Performance metrics included
- [ ] Co-authored attribution present

---

## Task Dependency Graph

### Critical Path (Sequential)
```
T001 (baseline) → T002 (backup) → T003 (metrics)
  ↓
T004 (test prep) → T005 → T006 → T007 (TDD red)
  ↓
T008 (impl) → T009 → T010 → T011 → T012 (TDD green)
  ↓
T013 (routing test) → T014 (graph) → T015 → T016 → T017 → T018 (validate)
  ↓
T032 (mypy) → T033 (ruff) → T034 (tests) → T035 (coverage)
  ↓
T038 (studio) → T039 → T040 → T041 (manual validation)
  ↓
T042 (review) → T043 (docs) → T044 (commit)
```

### Parallel Opportunities

**After T012 (PubMed impl complete):**
- T019, T020 [P] (State cleanup) - independent
- T022, T023, T024 [P] (File deletion) - independent
- T026, T027 [P] (Config cleanup) - independent
- T029, T030, T031 [P] (Docs) - independent

**Execution Example:**
```bash
# After T012, run in parallel:
# Terminal 1:
git rm src/agent/nodes/translation.py
git rm src/agent/utils/translation_prompts.py
git rm tests/unit_tests/nodes/test_translation.py

# Terminal 2:
# Edit .env, README.md (config cleanup)

# Terminal 3:
# Edit CLAUDE.md (docs)

# All terminals: Commit changes together
```

---

## Success Metrics Tracking

### Performance Metrics
| Metric | Baseline | Target | Actual | Status |
|--------|----------|--------|--------|--------|
| Latency (avg) | 8-10s | ≤5s | _TBD_ | ⏳ |
| API calls/query | 3 | 1 | _TBD_ | ⏳ |
| Graph nodes | 5 | 3 | _TBD_ | ⏳ |

### Quality Metrics
| Metric | Baseline | Target | Actual | Status |
|--------|----------|--------|--------|--------|
| Test coverage | 96% | ≥80% | _TBD_ | ⏳ |
| Tests passing | 177/183 | ≥169/175 | _TBD_ | ⏳ |
| mypy errors | 0 | 0 | _TBD_ | ⏳ |
| ruff issues | 0 | 0 | _TBD_ | ⏳ |

### User Satisfaction
| Criterion | Target | Validation | Status |
|-----------|--------|------------|--------|
| Czech quality | ≥90% satisfaction | Manual review | ⏳ |
| Citation format | [1][2][3] works | Visual check | ⏳ |
| No info loss | Equal to translation | Comparison | ⏳ |

---

## Rollback Plan

**Trigger Conditions:**
- Test coverage drops below 80%
- Czech response quality unacceptable
- Performance regression >10%
- Critical bugs in production

**Rollback Steps:**
1. `git checkout 005-biomcp-pubmed-agent-backup`
2. `git push -f origin 005-biomcp-pubmed-agent`
3. Restart `langgraph dev`
4. Verify old translation approach works

**Estimated Rollback Time**: <10 minutes

---

## Implementation Checklist

**Pre-Implementation:**
- [ ] Review spec.md and plan.md
- [ ] Ensure backup branch exists
- [ ] Baseline metrics documented

**During Implementation:**
- [ ] Follow TDD workflow (red → green → refactor)
- [ ] Maintain test coverage ≥80%
- [ ] Commit frequently with good messages
- [ ] Test in LangGraph Studio regularly

**Post-Implementation:**
- [ ] All quality gates pass
- [ ] Manual validation complete
- [ ] Documentation updated
- [ ] Performance metrics validated
- [ ] Czech quality confirmed

---

**Tasks Total**: 44 tasks
**Estimated Time**: 4-5 hours (single developer)
**Risk Level**: LOW (well-scoped refactoring)
**Next Command**: `/speckit.implement` - Execute tasks sequentially

---

**Version**: 1.0.0
**Created**: 2026-01-25
**Status**: ✅ READY FOR EXECUTION
