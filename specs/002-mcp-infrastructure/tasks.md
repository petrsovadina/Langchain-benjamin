# Feature Tasks: MCP Infrastructure

**Feature**: 002-mcp-infrastructure
**Created**: 2026-01-14
**Status**: Ready for Implementation
**Total Estimated**: 32 hours (4 days)

## Task Organization

Úkoly jsou organizovány podle **TDD workflow** a **Constitution Principle III** (Test-First Development):
- 🔴 **RED**: Napsat failing test
- 🟢 **GREEN**: Implementovat minimum pro passing test
- 🔵 **REFACTOR**: Vylepšit kód bez změny funkcionality

Každá fáze obsahuje atomické úkoly s odhadem času a acceptance criteria.

---

## Phase 1: Domain Core (Day 1 - 8 hours)

### 🎯 Phase Goal
Vytvořit framework-independent domain layer s pure Python entities a interfaces.

---

### Task 1.1: Setup MCP Package Structure
**Estimate**: 30 min
**Type**: Infrastructure
**Priority**: P1 (blocker for all other tasks)

**Description**:
Vytvořit adresářovou strukturu pro MCP infrastructure package.

**Steps**:
1. Vytvořit `langgraph-app/src/agent/mcp/` directory
2. Vytvořit `langgraph-app/src/agent/mcp/domain/` directory
3. Vytvořit `langgraph-app/src/agent/mcp/adapters/` directory
4. Vytvořit prázdné `__init__.py` soubory ve všech packages
5. Vytvořit `tests/unit_tests/mcp/` directory
6. Vytvořit `tests/integration_tests/mcp/` directory

**Acceptance Criteria**:
- [ ] Všechny directories existují
- [ ] Python může importovat: `from agent.mcp import ...`
- [ ] `pytest --collect-only` detekuje mcp test directories

**Files**:
- `src/agent/mcp/__init__.py`
- `src/agent/mcp/domain/__init__.py`
- `src/agent/mcp/adapters/__init__.py`
- `tests/unit_tests/mcp/__init__.py`
- `tests/integration_tests/mcp/__init__.py`

---

### Task 1.2: 🔴 RED - Write Tests for MCPResponse Entity
**Estimate**: 45 min
**Type**: Test-First
**Priority**: P1
**Depends on**: Task 1.1

**Description**:
Napsat failing unit tests pro MCPResponse value object podle spec.

**Steps**:
1. Vytvořit `tests/unit_tests/mcp/test_domain_entities.py`
2. Napsat test pro successful MCPResponse creation
3. Napsat test pro failed MCPResponse (must have error)
4. Napsat test pro immutability (frozen dataclass)
5. Napsat test pro metadata
6. Spustit `pytest` - všechny testy MUSÍ failovat (RED)

**Acceptance Criteria**:
- [ ] Soubor `test_domain_entities.py` existuje
- [ ] 4+ test cases pro MCPResponse
- [ ] `pytest tests/unit_tests/mcp/test_domain_entities.py` FAILS (RED phase)
- [ ] Tests používají pytest fixtures a parametrize kde vhodné

**Example Test**:
```python
def test_successful_mcp_response():
    response = MCPResponse(
        success=True,
        data={"drugs": [{"name": "Aspirin"}]},
        metadata={"latency_ms": 50}
    )
    assert response.success is True
    assert response.data["drugs"][0]["name"] == "Aspirin"
```

---

### Task 1.3: 🟢 GREEN - Implement MCPResponse Entity
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 1.2

**Description**:
Implementovat MCPResponse dataclass pro passing tests.

**Steps**:
1. Vytvořit `src/agent/mcp/domain/entities.py`
2. Implementovat `MCPResponse` jako frozen dataclass
3. Přidat `__post_init__` validaci (failed needs error)
4. Přidat type hints pro všechny fields
5. Spustit testy - MUSÍ být zelené (GREEN)

**Acceptance Criteria**:
- [ ] `pytest tests/unit_tests/mcp/test_domain_entities.py::test_mcp_response*` PASSES
- [ ] `mypy --strict src/agent/mcp/domain/entities.py` - 0 errors
- [ ] MCPResponse je frozen (immutable)

**Files**:
- `src/agent/mcp/domain/entities.py` (nový)

---

### Task 1.4: 🔴 RED - Write Tests for RetryConfig
**Estimate**: 30 min
**Type**: Test-First
**Priority**: P1
**Depends on**: Task 1.3

**Description**:
Napsat failing tests pro RetryConfig s validací.

**Steps**:
1. Přidat test cases do `test_domain_entities.py`
2. Test default config values
3. Test invalid max_retries (negative)
4. Test max_delay < base_delay validation
5. Test jitter boolean
6. Spustit testy - nové MUSÍ failovat

**Acceptance Criteria**:
- [ ] 4+ test cases pro RetryConfig
- [ ] Tests pokrývají validation errors (ValueError)
- [ ] `pytest` FAILS na nových testech

---

### Task 1.5: 🟢 GREEN - Implement RetryConfig Entity
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 1.4

**Description**:
Implementovat RetryConfig dataclass s validací.

**Steps**:
1. Přidat `RetryConfig` do `entities.py`
2. Implementovat `__post_init__` validaci
3. Nastavit default values (max_retries=3, base_delay=1.0, atd.)
4. Run tests - MUSÍ projít

**Acceptance Criteria**:
- [ ] `pytest tests/unit_tests/mcp/test_domain_entities.py::test_retry_config*` PASSES
- [ ] Validation raise ValueError s popisnou zprávou
- [ ] mypy --strict clean

---

### Task 1.6: 🟢 GREEN - Implement MCPHealthStatus Entity
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 1.5

**Description**:
Implementovat MCPHealthStatus (TDD zkrácený cyklus - jednoduchá entita).

**Steps**:
1. Napsat 3 testy pro MCPHealthStatus (healthy, unavailable, timeout)
2. Implementovat jako frozen dataclass
3. Literal type pro status field
4. Verify tests pass

**Acceptance Criteria**:
- [ ] MCPHealthStatus má Literal["healthy", "unhealthy", "unavailable", "timeout"]
- [ ] Tests pro všechny stavy
- [ ] Frozen dataclass

**Files**:
- Update `src/agent/mcp/domain/entities.py`
- Update `tests/unit_tests/mcp/test_domain_entities.py`

---

### Task 1.7: 🟢 GREEN - Implement MCPToolMetadata Entity
**Estimate**: 20 min
**Type**: Implementation
**Priority**: P2
**Depends on**: Task 1.6

**Description**:
Implementovat MCPToolMetadata pro tool discovery.

**Steps**:
1. Napsat basic test (name, description)
2. Implementovat jako frozen dataclass
3. Fields: name, description, parameters, returns

**Acceptance Criteria**:
- [ ] MCPToolMetadata vytvoření funguje
- [ ] Frozen dataclass
- [ ] Type hints

---

### Task 1.8: 🔴 RED - Write Tests for Domain Exceptions
**Estimate**: 30 min
**Type**: Test-First
**Priority**: P1
**Depends on**: Task 1.7

**Description**:
Napsat testy pro custom MCP exceptions.

**Steps**:
1. Vytvořit `tests/unit_tests/mcp/test_exceptions.py`
2. Test MCPConnectionError (has server_url)
3. Test MCPTimeoutError
4. Test MCPValidationError (has validation_errors list)
5. Test MCPServerError (has status_code)
6. Test exception inheritance (all inherit from MCPError)

**Acceptance Criteria**:
- [ ] 5+ test cases pro exceptions
- [ ] Tests ověřují custom attributes
- [ ] Tests ověřují inheritance chain

---

### Task 1.9: 🟢 GREEN - Implement Domain Exceptions
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 1.8

**Description**:
Implementovat custom exception hierarchy.

**Steps**:
1. Vytvořit `src/agent/mcp/domain/exceptions.py`
2. Implementovat MCPError base class
3. Implementovat 4 specifické exceptions
4. Přidat custom attributes (server_url, status_code, atd.)
5. Verify tests pass

**Acceptance Criteria**:
- [ ] `pytest tests/unit_tests/mcp/test_exceptions.py` PASSES
- [ ] Všechny exceptions inherit from MCPError
- [ ] mypy --strict clean

**Files**:
- `src/agent/mcp/domain/exceptions.py` (nový)

---

### Task 1.10: 🔴 RED - Write Tests for IMCPClient Port
**Estimate**: 45 min
**Type**: Test-First
**Priority**: P1
**Depends on**: Task 1.9

**Description**:
Napsat testy pro IMCPClient abstract interface.

**Steps**:
1. Vytvořit `tests/unit_tests/mcp/test_ports.py`
2. Test cannot instantiate IMCPClient (ABC)
3. Test concrete implementation must implement all methods
4. Test method signatures (type hints)
5. Mock implementation pro testing

**Acceptance Criteria**:
- [ ] Tests ověřují ABC behavior
- [ ] Tests definují expected method signatures
- [ ] Mock client pro testování

---

### Task 1.11: 🟢 GREEN - Implement IMCPClient Port
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 1.10

**Description**:
Implementovat IMCPClient abstract base class.

**Steps**:
1. Vytvořit `src/agent/mcp/domain/ports.py`
2. Implementovat IMCPClient(ABC)
3. Abstract methods: call_tool, health_check, list_tools, close
4. Type hints pro všechny methods
5. Docstrings podle Google style

**Acceptance Criteria**:
- [ ] `pytest tests/unit_tests/mcp/test_ports.py` PASSES
- [ ] IMCPClient je ABC s @abstractmethod
- [ ] Všechny methods mají type hints a docstrings
- [ ] mypy --strict clean

**Files**:
- `src/agent/mcp/domain/ports.py` (nový)

---

### Task 1.12: 🟢 GREEN - Implement IRetryStrategy Port
**Estimate**: 20 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 1.11

**Description**:
Implementovat IRetryStrategy interface (zkrácený TDD - jednoduchý port).

**Steps**:
1. Přidat test do `test_ports.py`
2. Implementovat IRetryStrategy(ABC)
3. Abstract method: execute_with_retry

**Acceptance Criteria**:
- [ ] IRetryStrategy je ABC
- [ ] execute_with_retry má type hints
- [ ] Tests pass

---

### ✅ Phase 1 Completion Checklist

Po dokončení všech úkolů Phase 1:
- [ ] Všechny domain entity testy PASS (100%)
- [ ] `mypy --strict src/agent/mcp/domain/` - 0 errors
- [ ] `ruff check src/agent/mcp/domain/` - 0 errors
- [ ] Code coverage pro domain/ ≥95%
- [ ] Git commit: `feat(mcp): implement domain core entities and ports`

**Phase 1 Output**:
- ✅ 3 entities (MCPResponse, RetryConfig, MCPHealthStatus)
- ✅ 1 metadata (MCPToolMetadata)
- ✅ 2 ports (IMCPClient, IRetryStrategy)
- ✅ 4 exceptions (MCPConnectionError, MCPTimeoutError, MCPValidationError, MCPServerError)
- ✅ ~15 unit tests

---

## Phase 2: SÚKL MCP Client Adapter (Day 2 Morning - 5 hours)

### 🎯 Phase Goal
Implementovat SUKLMCPClient adapter s aiohttp a retry logic.

---

### Task 2.1: Install Dependencies
**Estimate**: 15 min
**Type**: Infrastructure
**Priority**: P1
**Depends on**: Phase 1 complete

**Description**:
Přidat MCP dependencies do pyproject.toml.

**Steps**:
1. Otevřít `langgraph-app/pyproject.toml`
2. Přidat do `dependencies`: aiohttp>=3.9.0, tenacity>=8.2.0, pydantic>=2.5.0
3. Přidat do `dev` dependencies: aioresponses>=0.7.6
4. Spustit `pip install -e .` nebo `uv pip install -e .`

**Acceptance Criteria**:
- [ ] `python -c "import aiohttp; import tenacity; import pydantic"` funguje
- [ ] `pytest` může importovat aioresponses
- [ ] pyproject.toml správně naformátován

**Files**:
- `langgraph-app/pyproject.toml` (update)

---

### Task 2.2: 🔴 RED - Write Tests for SUKLMCPClient Initialization
**Estimate**: 30 min
**Type**: Test-First
**Priority**: P1
**Depends on**: Task 2.1

**Description**:
Napsat testy pro SUKLMCPClient konstruktor a lazy session init.

**Steps**:
1. Vytvořit `tests/unit_tests/mcp/test_sukl_client.py`
2. Test __init__ s default parameters
3. Test __init__ s custom base_url, timeout
4. Test lazy session initialization (_get_session)
5. Test session reuse (stejná instance)

**Acceptance Criteria**:
- [ ] 4+ test cases pro initialization
- [ ] Tests FAIL (SUKLMCPClient neexistuje)
- [ ] Tests používají pytest-asyncio

---

### Task 2.3: 🟢 GREEN - Implement SUKLMCPClient Basic Structure
**Estimate**: 45 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 2.2

**Description**:
Vytvořit SUKLMCPClient skeleton s lazy session.

**Steps**:
1. Vytvořit `src/agent/mcp/adapters/sukl_client.py`
2. Implementovat `SUKLMCPClient(IMCPClient)`
3. __init__ method s parameters
4. _get_session() async method (lazy aiohttp session)
5. Stub methods pro IMCPClient interface (raise NotImplementedError)

**Acceptance Criteria**:
- [ ] `pytest tests/unit_tests/mcp/test_sukl_client.py::test_init*` PASSES
- [ ] SUKLMCPClient implements IMCPClient
- [ ] mypy --strict clean

**Files**:
- `src/agent/mcp/adapters/sukl_client.py` (nový)

---

### Task 2.4: 🔴 RED - Write Tests for call_tool Method
**Estimate**: 1 hour
**Type**: Test-First
**Priority**: P1
**Depends on**: Task 2.3

**Description**:
Napsat comprehensive testy pro SUKLMCPClient.call_tool s aioresponses.

**Steps**:
1. Přidat tests do `test_sukl_client.py`
2. Test successful call (200 OK)
3. Test connection error (ClientConnectorError)
4. Test timeout error (ServerTimeoutError)
5. Test 5xx server error (should raise MCPServerError)
6. Test 429 rate limiting (should raise MCPTimeoutError)
7. Test 400 client error (return MCPResponse with success=False)
8. Test metadata in response (latency_ms)

**Acceptance Criteria**:
- [ ] 7+ test cases pro call_tool
- [ ] Uses aioresponses for HTTP mocking
- [ ] Tests pokrývají všechny error scénáře
- [ ] Tests FAIL (call_tool not implemented)

**Example Test**:
```python
@pytest.mark.asyncio
async def test_call_tool_success():
    with aioresponses() as m:
        m.post(
            "http://test:3000/tools/search_drugs",
            payload={"drugs": [{"name": "Aspirin"}]}
        )

        client = SUKLMCPClient(base_url="http://test:3000")
        response = await client.call_tool("search_drugs", {"query": "aspirin"})

        assert response.success is True
        assert response.data["drugs"][0]["name"] == "Aspirin"
```

---

### Task 2.5: 🟢 GREEN - Implement call_tool Method
**Estimate**: 1.5 hours
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 2.4

**Description**:
Implementovat SUKLMCPClient.call_tool s error handling.

**Steps**:
1. Implementovat async call_tool method
2. HTTP POST k `{base_url}/tools/{tool_name}`
3. Error handling pro všechny exception types
4. Transform exceptions na MCP* errors
5. Přidat metadata (latency_ms, server_url)
6. Logging (DEBUG level)

**Acceptance Criteria**:
- [ ] `pytest tests/unit_tests/mcp/test_sukl_client.py::test_call_tool*` PASSES
- [ ] Všechny exception paths pokryté
- [ ] Logging přítomen
- [ ] mypy --strict clean

---

### Task 2.6: 🔴🟢 RED+GREEN - Implement health_check Method
**Estimate**: 45 min
**Type**: TDD (fast cycle)
**Priority**: P1
**Depends on**: Task 2.5

**Description**:
TDD pro health_check method (zkrácený cyklus).

**Steps**:
1. Napsat 4 tests: healthy, unhealthy, unavailable, timeout
2. Implementovat health_check method
3. GET request na `{base_url}/health`
4. Return MCPHealthStatus

**Acceptance Criteria**:
- [ ] Tests PASS
- [ ] health_check má timeout parameter
- [ ] Vrací všechny status types

---

### Task 2.7: 🟢 GREEN - Implement search_drugs Helper
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P2
**Depends on**: Task 2.6

**Description**:
Implementovat typed helper method pro search_drugs.

**Steps**:
1. Vytvořit Pydantic model DrugSearchResult
2. Implementovat search_drugs method
3. Volá call_tool("search_drugs", ...)
4. Validate response s Pydantic
5. Return typed List[DrugSearchResult]

**Acceptance Criteria**:
- [ ] search_drugs vrací typed list
- [ ] Pydantic validation funguje
- [ ] Test pokrývá happy path

---

### Task 2.8: 🟢 GREEN - Implement list_tools and close Methods
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P2
**Depends on**: Task 2.7

**Description**:
Dokončit zbývající IMCPClient methods.

**Steps**:
1. Implementovat list_tools (hardcoded pro 8 SÚKL tools)
2. Implementovat close method (close aiohttp session)
3. Napsat basic tests

**Acceptance Criteria**:
- [ ] list_tools vrací 8 MCPToolMetadata
- [ ] close zavře session
- [ ] Tests pass

---

### ✅ Phase 2 Completion Checklist

- [ ] SUKLMCPClient tests PASS (100%)
- [ ] Code coverage ≥90%
- [ ] mypy --strict clean
- [ ] ruff check clean
- [ ] Git commit: `feat(mcp): implement SUKLMCPClient adapter`

**Phase 2 Output**:
- ✅ SUKLMCPClient fully functional
- ✅ ~12 unit tests s aioresponses
- ✅ Error handling comprehensive

---

## Phase 3: BioMCP Client Adapter (Day 2 Afternoon - 5 hours)

### 🎯 Phase Goal
Implementovat BioMCPClient adapter (similar pattern to SÚKL).

---

### Task 3.1: 🔴 RED - Write Tests for BioMCPClient
**Estimate**: 1 hour
**Type**: Test-First
**Priority**: P1
**Depends on**: Phase 2 complete

**Description**:
Napsat testy pro BioMCPClient (reuse pattern ze SÚKL).

**Steps**:
1. Vytvořit `tests/unit_tests/mcp/test_biomcp_client.py`
2. Copy test structure z test_sukl_client.py
3. Adapt pro BioMCP URLs a responses
4. Focus na 3 tools: article_searcher, get_full_text, search_trials

**Acceptance Criteria**:
- [ ] 10+ test cases (init, call_tool, helpers)
- [ ] Tests FAIL (BioMCPClient neexistuje)

---

### Task 3.2: 🟢 GREEN - Implement BioMCPClient
**Estimate**: 2 hours
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 3.1

**Description**:
Implementovat BioMCPClient (copy-adapt pattern ze SUKLMCPClient).

**Steps**:
1. Vytvořit `src/agent/mcp/adapters/biomcp_client.py`
2. Copy SUKLMCPClient structure
3. Adapt base_url default (localhost:8080)
4. Adapt timeout default (60s)
5. Add max_results parameter
6. Implement call_tool, health_check, close (same pattern)

**Acceptance Criteria**:
- [ ] `pytest tests/unit_tests/mcp/test_biomcp_client.py` PASSES
- [ ] BioMCPClient implements IMCPClient
- [ ] mypy --strict clean

**Files**:
- `src/agent/mcp/adapters/biomcp_client.py` (nový)

---

### Task 3.3: 🟢 GREEN - Implement BioMCP Pydantic Models
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 3.2

**Description**:
Vytvořit Pydantic models pro BioMCP responses.

**Steps**:
1. Přidat do biomcp_client.py:
   - PubMedArticle model (pmid, title, abstract, authors, doi)
   - ClinicalTrial model (nct_id, title, status, phase)
2. Test models s sample data

**Acceptance Criteria**:
- [ ] Pydantic models validate correctly
- [ ] Optional fields správně nakonfigurovány
- [ ] Tests pass

---

### Task 3.4: 🟢 GREEN - Implement Typed Helper Methods
**Estimate**: 1 hour
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 3.3

**Description**:
Implementovat 3 top helper methods.

**Steps**:
1. search_articles(query, max_results) → List[PubMedArticle]
2. get_full_text(pmid) → Optional[str]
3. search_trials(query) → List[ClinicalTrial]
4. Validate responses s Pydantic
5. Tests pro všechny 3 methods

**Acceptance Criteria**:
- [ ] Všechny 3 helpers fungují
- [ ] Return typed data
- [ ] Tests pass s aioresponses

---

### Task 3.5: 🔵 REFACTOR - Extract Common Client Logic
**Estimate**: 30 min
**Type**: Refactoring
**Priority**: P2
**Depends on**: Task 3.4

**Description**:
Refactor duplicitní kód mezi SÚKL a BioMCP clients.

**Steps**:
1. Identifikovat common patterns (session management, error handling)
2. Zvážit abstract BaseMCPClient class
3. Refactor pokud to zlepší maintainability
4. **DŮLEŽITÉ**: Verify všechny tests stále PASS po refactoru

**Acceptance Criteria**:
- [ ] Žádné testy nesmí failovat po refactoru
- [ ] Code coverage nesmí klesnout
- [ ] mypy --strict clean

---

### ✅ Phase 3 Completion Checklist

- [ ] BioMCPClient tests PASS (100%)
- [ ] Code coverage ≥90%
- [ ] mypy --strict clean
- [ ] Git commit: `feat(mcp): implement BioMCPClient adapter`

**Phase 3 Output**:
- ✅ BioMCPClient fully functional
- ✅ 3 typed helpers (search_articles, get_full_text, search_trials)
- ✅ Pydantic validation
- ✅ ~10 unit tests

---

## Phase 4: Retry Strategy (Day 3 Morning - 4 hours)

### 🎯 Phase Goal
Implementovat TenacityRetryStrategy s exponential backoff.

---

### Task 4.1: 🔴 RED - Write Tests for TenacityRetryStrategy
**Estimate**: 1 hour
**Type**: Test-First
**Priority**: P1
**Depends on**: Phase 3 complete

**Description**:
Napsat testy pro retry behavior.

**Steps**:
1. Vytvořit `tests/unit_tests/mcp/test_retry_strategy.py`
2. Test operation succeeds after 2 failures
3. Test max retries exhausted (raises original exception)
4. Test exponential backoff delays (mock time.sleep)
5. Test jitter adds randomness
6. Test only retries transient errors (not ValidationError)
7. Test respects RetryConfig

**Acceptance Criteria**:
- [ ] 6+ test cases pro retry logic
- [ ] Uses AsyncMock pro operations
- [ ] Tests measure retry counts
- [ ] Tests FAIL (TenacityRetryStrategy neexistuje)

**Example Test**:
```python
@pytest.mark.asyncio
async def test_succeeds_after_failures():
    strategy = TenacityRetryStrategy()
    config = RetryConfig(max_retries=3, base_delay=0.01)

    call_count = 0
    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise MCPConnectionError("Fail")
        return {"ok": True}

    result = await strategy.execute_with_retry(flaky, config)

    assert result == {"ok": True}
    assert call_count == 3
```

---

### Task 4.2: 🟢 GREEN - Implement TenacityRetryStrategy
**Estimate**: 1.5 hours
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 4.1

**Description**:
Implementovat retry strategy s Tenacity library.

**Steps**:
1. Vytvořit `src/agent/mcp/adapters/retry_strategy.py`
2. Implementovat TenacityRetryStrategy(IRetryStrategy)
3. execute_with_retry method
4. Build Tenacity retry decorator dynamically z RetryConfig
5. retry_if_exception_type pro MCPConnectionError, MCPTimeoutError, MCPServerError
6. wait_exponential s jitter
7. Logging (before_sleep_log)

**Acceptance Criteria**:
- [ ] `pytest tests/unit_tests/mcp/test_retry_strategy.py` PASSES
- [ ] Exponential backoff funguje
- [ ] Jitter adds randomness (±20%)
- [ ] mypy --strict clean

**Files**:
- `src/agent/mcp/adapters/retry_strategy.py` (nový)

---

### Task 4.3: 🟢 GREEN - Integrate Retry Strategy with Clients
**Estimate**: 1 hour
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 4.2

**Description**:
Připojit TenacityRetryStrategy k SÚKL a BioMCP clients.

**Steps**:
1. Update SUKLMCPClient.__init__ přidat retry_strategy parameter
2. Update call_tool použít retry_strategy.execute_with_retry
3. Repeat pro BioMCPClient
4. Update tests pro retry behavior
5. Integration test s mock failures

**Acceptance Criteria**:
- [ ] Clients používají retry strategy
- [ ] Tests pro retried calls PASS
- [ ] Default RetryConfig used pokud není provided

---

### Task 4.4: 🔵 REFACTOR - Optimize Retry Configuration
**Estimate**: 30 min
**Type**: Refactoring
**Priority**: P2
**Depends on**: Task 4.3

**Description**:
Fine-tune retry config defaults based na testing.

**Steps**:
1. Review retry delays (jsou rozumné?)
2. Test různé configs (fast fail vs patient retry)
3. Document best practices v docstrings
4. Verify všechny tests PASS

**Acceptance Criteria**:
- [ ] Default configs dokumentované
- [ ] Tests pass
- [ ] No performance regression

---

### ✅ Phase 4 Completion Checklist

- [ ] TenacityRetryStrategy tests PASS (100%)
- [ ] Integrated s SÚKL a BioMCP clients
- [ ] Code coverage ≥90%
- [ ] Git commit: `feat(mcp): implement retry strategy with exponential backoff`

**Phase 4 Output**:
- ✅ TenacityRetryStrategy fully functional
- ✅ Exponential backoff + jitter
- ✅ Clients support retry
- ✅ ~6 unit tests

---

## Phase 5: Configuration & Integration (Day 3 Afternoon - 4 hours)

### 🎯 Phase Goal
Setup environment configuration a integrace s Feature 001.

---

### Task 5.1: 🟢 GREEN - Implement MCPConfig
**Estimate**: 45 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Phase 4 complete

**Description**:
Vytvořit MCPConfig dataclass pro .env loading.

**Steps**:
1. Vytvořit `src/agent/mcp/config.py`
2. Implementovat MCPConfig dataclass
3. from_env() classmethod s os.getenv
4. Fallback defaults pro všechny values
5. Type validation (float, int conversions)

**Acceptance Criteria**:
- [ ] MCPConfig.from_env() funguje
- [ ] Defaults správně nastaveny
- [ ] Type conversions fungují
- [ ] Test s mock environment variables

**Files**:
- `src/agent/mcp/config.py` (nový)

---

### Task 5.2: Create .env.example for MCP
**Estimate**: 15 min
**Type**: Documentation
**Priority**: P1
**Depends on**: Task 5.1

**Description**:
Přidat MCP variables do .env.example.

**Steps**:
1. Otevřít `langgraph-app/.env.example`
2. Přidat sekci "# MCP Infrastructure Configuration"
3. Add všechny env vars s comments
4. Document defaults

**Acceptance Criteria**:
- [ ] .env.example má všechny MCP vars
- [ ] Comments vysvětlují purpose
- [ ] Defaults dokumentovány

**Files**:
- `langgraph-app/.env.example` (update)

---

### Task 5.3: 🟢 GREEN - Implement Public API (__init__.py)
**Estimate**: 30 min
**Type**: Implementation
**Priority**: P1
**Depends on**: Task 5.2

**Description**:
Vytvořit clean public API pro MCP package.

**Steps**:
1. Update `src/agent/mcp/__init__.py`
2. Import all public classes (MCPResponse, SUKLMCPClient, atd.)
3. Define __all__ list
4. Verify clean imports fungují

**Acceptance Criteria**:
- [ ] `from agent.mcp import SUKLMCPClient` funguje
- [ ] `from agent.mcp import *` importuje pouze public API
- [ ] Docstring v __init__.py s usage example

**Files**:
- `src/agent/mcp/__init__.py` (update)

---

### Task 5.4: 🟢 GREEN - Update Feature 001 Context
**Estimate**: 45 min
**Type**: Integration
**Priority**: P1
**Depends on**: Task 5.3

**Description**:
Aktualizovat Context v graph.py pro typed MCP clients.

**Steps**:
1. Otevřít `src/agent/graph.py`
2. Update Context TypedDict:
   - Change `sukl_mcp_client: Any` → `sukl_mcp_client: SUKLMCPClient`
   - Change `biomcp_client: Any` → `biomcp_client: BioMCPClient`
3. Add import statements
4. Create example runtime context factory
5. Update docstrings

**Acceptance Criteria**:
- [ ] Context má typed MCP clients
- [ ] mypy --strict passes na graph.py
- [ ] Example factory funguje

**Files**:
- `src/agent/graph.py` (update)

---

### Task 5.5: Write MCP Integration Documentation
**Estimate**: 1 hour
**Type**: Documentation
**Priority**: P2
**Depends on**: Task 5.4

**Description**:
Vytvořit docs/MCP_INTEGRATION.md guide.

**Steps**:
1. Vytvořit `langgraph-app/docs/MCP_INTEGRATION.md`
2. Document SÚKL-mcp setup (git clone, npm start)
3. Document BioMCP Docker setup (docker-compose)
4. Usage examples (SUKLMCPClient, BioMCPClient)
5. Troubleshooting section
6. Environment variables reference

**Acceptance Criteria**:
- [ ] MCP_INTEGRATION.md existuje
- [ ] Includes setup instructions
- [ ] Includes code examples
- [ ] Markdown well-formatted

**Files**:
- `langgraph-app/docs/MCP_INTEGRATION.md` (nový)

---

### ✅ Phase 5 Completion Checklist

- [ ] MCPConfig funguje s .env
- [ ] Feature 001 Context updated
- [ ] Documentation complete
- [ ] Git commit: `feat(mcp): add configuration and Feature 001 integration`

**Phase 5 Output**:
- ✅ MCPConfig s .env support
- ✅ Updated Context (typed clients)
- ✅ Documentation

---

## Phase 6: Integration Tests (Day 4 - 6 hours)

### 🎯 Phase Goal
Napsat integration tests s reálnými MCP servery.

---

### Task 6.1: Setup SÚKL-mcp Test Server
**Estimate**: 30 min
**Type**: Infrastructure
**Priority**: P1
**Depends on**: Phase 5 complete

**Description**:
Setup SÚKL-mcp server pro integration testing.

**Steps**:
1. Clone https://github.com/petrsovadina/SUKL-mcp
2. `npm install && npm start`
3. Verify běží na localhost:3000
4. Test basic endpoint (curl http://localhost:3000/health)
5. Document setup v README

**Acceptance Criteria**:
- [ ] SÚKL-mcp server běží
- [ ] Health endpoint odpovídá
- [ ] Port 3000 available

---

### Task 6.2: Setup BioMCP Docker Container
**Estimate**: 30 min
**Type**: Infrastructure
**Priority**: P1
**Depends on**: Task 6.1

**Description**:
Setup BioMCP v Docker pro testing.

**Steps**:
1. Create docker-compose.yml pro BioMCP
2. `docker-compose up -d biomcp`
3. Verify běží na localhost:8080
4. Test article_searcher endpoint
5. Document v README

**Acceptance Criteria**:
- [ ] BioMCP container běží
- [ ] Port 8080 accessible
- [ ] API responds

---

### Task 6.3: 🔴 RED - Write SÚKL Integration Tests
**Estimate**: 1 hour
**Type**: Test-First
**Priority**: P1
**Depends on**: Task 6.2

**Description**:
Napsat integration tests proti real SÚKL server.

**Steps**:
1. Vytvořit `tests/integration_tests/mcp/test_sukl_integration.py`
2. Test real drug search (aspirin)
3. Test health check
4. Test all 8 tools (pokud možné)
5. Test error handling (invalid query)
6. Mark s @pytest.mark.integration

**Acceptance Criteria**:
- [ ] 5+ integration test cases
- [ ] Tests use real SUKLMCPClient
- [ ] Tests marked s @pytest.mark.integration
- [ ] Tests SKIP if server not available

**Example Test**:
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_sukl_drug_search():
    config = MCPConfig.from_env()
    client = SUKLMCPClient(base_url=config.sukl_url)

    drugs = await client.search_drugs("aspirin")

    assert len(drugs) > 0
    assert any("aspirin" in d.name.lower() for d in drugs)

    await client.close()
```

---

### Task 6.4: 🟢 GREEN - Verify SÚKL Integration Tests Pass
**Estimate**: 1 hour
**Type**: Testing
**Priority**: P1
**Depends on**: Task 6.3

**Description**:
Fix any issues discovered in integration testing.

**Steps**:
1. Run `pytest -m integration tests/integration_tests/mcp/test_sukl_integration.py`
2. Debug any failures
3. Fix client implementation bugs
4. Verify ALL tests PASS

**Acceptance Criteria**:
- [ ] ALL integration tests PASS
- [ ] No flaky tests
- [ ] Reasonable execution time (<30s total)

---

### Task 6.5: 🔴🟢 RED+GREEN - Write BioMCP Integration Tests
**Estimate**: 1.5 hours
**Type**: TDD (fast cycle)
**Priority**: P1
**Depends on**: Task 6.4

**Description**:
Integration tests pro BioMCP (similar pattern).

**Steps**:
1. Vytvořit `tests/integration_tests/mcp/test_biomcp_integration.py`
2. Write tests (article search, full text, trials)
3. Run a fix any failures
4. Verify PASS

**Acceptance Criteria**:
- [ ] 5+ BioMCP integration tests
- [ ] Tests PASS
- [ ] Mark s @pytest.mark.integration

**Files**:
- `tests/integration_tests/mcp/test_biomcp_integration.py` (nový)

---

### Task 6.6: Write Health Check Integration Tests
**Estimate**: 45 min
**Type**: Testing
**Priority**: P2
**Depends on**: Task 6.5

**Description**:
Test health checks against real servers.

**Steps**:
1. Vytvořit `tests/integration_tests/mcp/test_health_checks.py`
2. Test SÚKL health (healthy, latency)
3. Test BioMCP health
4. Test unavailable server (stop Docker, check status)
5. Test timeout

**Acceptance Criteria**:
- [ ] Health checks fungují
- [ ] Detects unavailable servers
- [ ] Tests PASS

---

### Task 6.7: Measure and Optimize Performance
**Estimate**: 1 hour
**Type**: Performance
**Priority**: P2
**Depends on**: Task 6.6

**Description**:
Validate SC-001 (performance targets) a optimize.

**Steps**:
1. Write performance test (10 concurrent requests)
2. Measure latency (p50, p95, p99)
3. Measure throughput (requests/second)
4. Verify meets SC-001 (<500ms @ p95)
5. Verify meets SC-010 (≥50 req/s)
6. Profile a optimize pokud needed

**Acceptance Criteria**:
- [ ] p95 latency <500ms for SÚKL
- [ ] Throughput ≥50 req/s
- [ ] Performance test documented

---

### ✅ Phase 6 Completion Checklist

- [ ] ALL integration tests PASS
- [ ] Performance targets met (SC-001, SC-010)
- [ ] SÚKL-mcp a BioMCP servers dokumentovány
- [ ] Git commit: `test(mcp): add integration tests with real MCP servers`

**Phase 6 Output**:
- ✅ 15+ integration tests
- ✅ Performance validated
- ✅ Real server integration verified

---

## Final Quality Gates

### Quality Gate 1: Code Coverage
**Command**: `pytest --cov=src/agent/mcp --cov-report=term`

**Targets**:
- [ ] Overall coverage ≥90% (SC-006)
- [ ] domain/ coverage ≥95%
- [ ] adapters/ coverage ≥90%

---

### Quality Gate 2: Type Safety
**Command**: `mypy --strict src/agent/mcp`

**Targets**:
- [ ] 0 mypy errors (SC-005)
- [ ] All public API typed
- [ ] No `Any` without justification

---

### Quality Gate 3: Linting
**Command**: `ruff check src/agent/mcp tests/`

**Targets**:
- [ ] 0 ruff errors
- [ ] Code formatted (ruff format)
- [ ] Imports sorted

---

### Quality Gate 4: Documentation
**Checklist**:
- [ ] All public classes have docstrings (Google style)
- [ ] All public methods have docstrings
- [ ] MCP_INTEGRATION.md complete
- [ ] .env.example updated
- [ ] README.md mentions MCP infrastructure

---

### Quality Gate 5: Integration Tests
**Command**: `pytest -m integration`

**Targets**:
- [ ] ALL integration tests PASS
- [ ] SÚKL-mcp server accessible
- [ ] BioMCP Docker accessible
- [ ] Performance targets met

---

## Final Commit & PR

### Task F.1: Final Review & Commit
**Estimate**: 30 min
**Type**: Review
**Priority**: P1

**Steps**:
1. Review ALL code changes
2. Run ALL quality gates
3. Fix any remaining issues
4. Create final commit:
   ```bash
   git add .
   git commit -m "feat(mcp): Feature 002 - MCP Infrastructure complete

   - Implement Hexagonal Architecture (Ports & Adapters)
   - SUKLMCPClient with 8 tools
   - BioMCPClient with top 3 tools
   - TenacityRetryStrategy with exponential backoff
   - MCPConfig for .env management
   - 90%+ test coverage (unit + integration)
   - Type-safe (mypy --strict clean)

   Closes #002"
   ```

**Acceptance Criteria**:
- [ ] ALL quality gates PASS
- [ ] Commit message follows convention
- [ ] No uncommitted changes

---

### Task F.2: Create Pull Request
**Estimate**: 15 min
**Type**: Documentation
**Priority**: P1

**Steps**:
1. Push branch: `git push -u origin 002-mcp-infrastructure`
2. Create PR na GitHub/GitLab
3. Fill PR template:
   - Summary (link spec.md)
   - Changes (link plan.md)
   - Testing (screenshots/logs)
   - Checklist (all quality gates)

**Acceptance Criteria**:
- [ ] PR created
- [ ] CI passes
- [ ] Ready for review

---

## Success Criteria Validation

Po dokončení všech tasků, validate proti spec.md:

| SC | Criterion | Status | Evidence |
|----|-----------|--------|----------|
| SC-001 | <500ms @ p95 | ⬜ | Performance test results |
| SC-002 | ≥80% precision | ⬜ | BioMCP integration tests |
| SC-003 | 95% retry success | ⬜ | Retry strategy unit tests |
| SC-004 | 5s health check | ⬜ | Health check tests |
| SC-005 | 100% type coverage | ⬜ | mypy --strict output |
| SC-006 | ≥90% test coverage | ⬜ | pytest --cov report |
| SC-007 | 100% env load | ⬜ | MCPConfig tests |
| SC-008 | 8+3 examples | ⬜ | Docstrings count |
| SC-009 | User-friendly errors | ⬜ | Exception messages |
| SC-010 | ≥50 req/s | ⬜ | Throughput test results |

---

## Task Summary

**Total Tasks**: 45 atomických úkolů
**Total Time**: 32 hours (4 days)

**Breakdown**:
- Phase 1 (Domain Core): 12 tasks, 8h
- Phase 2 (SÚKL Client): 8 tasks, 5h
- Phase 3 (BioMCP Client): 5 tasks, 5h
- Phase 4 (Retry Strategy): 4 tasks, 4h
- Phase 5 (Config & Integration): 5 tasks, 4h
- Phase 6 (Integration Tests): 7 tasks, 6h
- Final (QA & PR): 2 tasks, 0.75h

**TDD Ratio**: ~60% RED-GREEN-REFACTOR cycles (Constitution compliant)

---

## Dependencies Graph

```
Phase 1 (Domain) → Phase 2 (SÚKL) → Phase 3 (BioMCP) → Phase 4 (Retry)
                                                              ↓
                                                        Phase 5 (Config)
                                                              ↓
                                                        Phase 6 (Tests)
                                                              ↓
                                                          Final QA
```

---

**Tasks Status**: ✅ **READY FOR IMPLEMENTATION**

**Next Action**: Start with Task 1.1 (Setup MCP Package Structure)

**Estimated Completion**: 2026-01-18 (4 pracovní dny od 2026-01-14)
