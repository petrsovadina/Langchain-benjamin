# Czech MedAI - Test Suite Audit Report
**Date:** 2026-02-16
**Audited by:** Claude Code (Expert Test Automation Engineer)
**Test Count:** 442 passing tests across ~11,384 lines of test code

---

## Executive Summary

Czech MedAI má solidní základ unit testů s 442 testy, ale **kriticky postrádá live integration tests, contract tests a smoke tests** pro externí služby. Všechny testy používají mocky - ani jeden test nekomunikuje se skutečným SÚKL MCP serverem (který je live na `https://sukl-mcp-ts.vercel.app/mcp`) nebo BioMCP.

### Critical Gaps
1. **Zero live service tests** - No validation that code works with real MCP servers
2. **No contract tests** - MCP server API changes would go undetected
3. **No SSE streaming tests** - Complex streaming logic is untested
4. **Minimal error scenario coverage** - Timeouts, malformed responses, partial failures
5. **No chaos/resilience tests** - System behavior under degraded conditions unknown

---

## 1. Fixture Quality Analysis (`tests/conftest.py`)

### ✅ Strengths

**Well-organized by feature:**
```python
# Feature 003: SÚKL Drug Agent Fixtures (lines 89-257)
# Feature 005: BioMCP PubMed Agent Fixtures (lines 259-417)
# Feature 006: Guidelines Agent Fixtures (lines 420-619)
# Feature 007: Supervisor Intent Classifier Fixtures (lines 621-705)
# Feature 009: Synthesizer Node Fixtures (lines 707-737)
```

**Realistic mock data:**
- `mock_sukl_response` returns multi-drug search results with proper structure
- `mock_biomcp_article` has complete PubMed metadata (PMID, DOI, authors, journal)
- `sample_guideline_sections` covers multiple sources (CLS-JEP, ESC)

**Smart fixture factories:**
- `create_mock_tool_call` factory (lines 638-674) - flexible LLM response creation
- `mock_sukl_client.call_tool.side_effect` (lines 176-206) - tool-aware responses

**Good use of `AsyncMock`:**
```python
client.call_tool = AsyncMock()  # Correct for async functions
```

### ⚠️ Weaknesses

**1. No fixture for live service testing:**
```python
# Missing:
@pytest.fixture(scope="session")
def live_sukl_client():
    """Real SÚKL MCP client for smoke tests."""
    return SUKLMCPClient(base_url="https://sukl-mcp-ts.vercel.app/mcp")
```

**2. Mock responses too simplistic:**
- Always return success (`success=True`)
- No fixtures for edge cases (empty results, malformed data, rate limiting)
- No simulation of real latencies (BioMCP can take 2-4s)

**3. `mock_runtime` fixture (lines 52-76):**
```python
class MockRuntime:
    def __init__(self):
        self.context = {
            "sukl_mcp_client": None,  # Always None!
            "biomcp_client": None,
        }
```
**Problem:** Tests must manually inject clients every time. Should provide pre-wired clients by default.

**4. Missing error fixtures:**
```python
# Should exist:
@pytest.fixture
def mock_sukl_timeout_error():
    client = MagicMock()
    client.call_tool = AsyncMock(side_effect=MCPTimeoutError("Request timeout"))
    return client

@pytest.fixture
def mock_sukl_malformed_response():
    # Simulate server returning unexpected JSON structure
    return MCPResponse(success=True, data={"unexpected": "schema"})
```

---

## 2. Unit Test Quality

### Analyzed Files:
- `test_supervisor.py` (927 lines, 74 test cases)
- `test_drug_agent.py` (443 lines, 25 test cases)

### ✅ Strengths

**Excellent test organization:**
```python
class TestIntentType:           # Enum validation (6 tests)
class TestIntentResult:         # Model validation (10 tests)
class TestIntentClassification: # All 8 intent types (8 tests)
class TestEdgeCases:           # Error handling (5 tests)
class TestSupervisorNode:      # Send API routing (16 tests)
```

**Test-Driven Development evidence:**
```python
# test_drug_agent.py has clear TDD structure:
# T021: Drug search functionality
# T022: Fuzzy matching behavior
# T023: Empty results handling
```

**Good coverage of LangGraph patterns:**
```python
@pytest.mark.asyncio
async def test_supervisor_node_compound_query(self, mock_runtime):
    # Tests Send API for parallel agent dispatch
    result = await supervisor_node(state, mock_runtime)

    assert isinstance(result, list)  # Multiple Send commands
    assert len(result) == 2
    node_names = {send.node for send in result}
    assert "drug_agent" in node_names
    assert "guidelines_agent" in node_names
```

**Proper mock isolation:**
```python
with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
    mock_classifier = MagicMock()
    mock_classifier.classify_intent = AsyncMock(return_value=mock_intent)
    mock_cls.return_value = mock_classifier
```

**Edge case coverage:**
```python
# test_supervisor.py (lines 316-385)
- Empty message raises ValueError
- Whitespace-only message raises ValueError
- LLM error triggers keyword fallback
- No tool_calls triggers keyword fallback
- Low confidence logs warning
```

### ⚠️ Weaknesses

**1. Testing mocks, not behavior:**
```python
# test_drug_agent.py (lines 64-78)
async def test_search_drugs_respects_limit(self, mock_sukl_client):
    query = DrugQuery(query_text="Paralen", query_type=QueryType.SEARCH, limit=5)
    await _search_drugs(mock_sukl_client, query)

    # Verifies that call_tool was called correctly
    mock_sukl_client.call_tool.assert_called_once()
    call_args = mock_sukl_client.call_tool.call_args
    assert call_args[0][1]["limit"] == 5  # ❌ Testing mock interaction
```

**Problem:** This verifies the mock was called, not that limit=5 actually works. If SÚKL MCP ignores the limit, test still passes.

**2. No timeout/latency tests:**
```python
# Missing:
@pytest.mark.asyncio
async def test_drug_agent_handles_slow_sukl_response():
    """Verify graceful handling of 10s+ SÚKL response time."""
    # Simulate 12s delay, expect timeout or progress indicator
```

**3. Error message tests are weak:**
```python
# test_drug_agent.py (lines 235-253)
async def test_drug_agent_node_handles_no_results(self, sample_state):
    result = await drug_agent_node(sample_state, mock_runtime)
    assert "nebyl nalezen" in result["messages"][0]["content"].lower()
```

**Problem:** Only checks for keyword presence, not full message quality or citation format.

**4. Missing concurrency tests:**
```python
# No tests for parallel agent execution via Send API
# No tests for race conditions in document aggregation
# No tests for concurrent MCP client usage
```

---

## 3. Integration Test Quality

### Analyzed Files:
- `test_api_server.py` (239 lines, 11 tests)
- `test_supervisor_flow.py` (164 lines, 4 tests)
- `test_synthesizer_flow.py` (428 lines, 13 tests)

### ✅ Strengths

**API tests use FastAPI TestClient:**
```python
def test_consult_endpoint_quick_mode(client: TestClient):
    response = client.post(
        "/api/v1/consult",
        json={"query": "Jaké jsou kontraindikace metforminu?", "mode": "quick"},
        headers={"Accept": "text/event-stream"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
```

**SSE event parsing:**
```python
events = []
for line in response.iter_lines():
    line = line.decode("utf-8")
    if line.startswith("data: "):
        data = json.loads(line[6:])
        events.append(data)

final_events = [e for e in events if e.get("type") == "final"]
assert len(final_events) == 1
```

**Health check tests:**
```python
def test_health_check_database_status(client):
    # Validates degraded status if database unavailable
    if database_status.startswith("error:"):
        assert data["status"] == "degraded"
```

### ⚠️ Critical Weaknesses

**1. NO real SSE streaming tests:**
```python
# test_api_server.py parses events from TestClient.iter_lines()
# BUT: TestClient returns entire response buffered, not true streaming
# Missing: Real async client that consumes SSE stream progressively
```

**Should have:**
```python
@pytest.mark.asyncio
async def test_consult_streaming_behavior():
    """Verify events arrive incrementally, not all at once."""
    async with httpx.AsyncClient() as client:
        async with client.stream("POST", "/api/v1/consult", json={...}) as response:
            events_received = []
            start_time = time.time()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    events_received.append((time.time() - start_time, json.loads(line[6:])))

            # Verify agent_start arrives before agent_complete
            assert events_received[0][1]["type"] == "agent_start"
            assert events_received[1][0] > events_received[0][0] + 0.5  # 500ms+ delay
```

**2. Integration tests still use mocks:**
```python
# test_supervisor_flow.py (lines 27-60)
with patch("agent.nodes.supervisor.IntentClassifier") as mock_cls:
    mock_classifier = MagicMock()
    # ... entire flow is mocked
    result = await graph.ainvoke(initial_state, config={...})
```

**Problem:** These are "integration" tests in name only - they're unit tests of graph wiring.

**3. No real MCP server tests:**
```python
# Missing:
@pytest.mark.live
@pytest.mark.asyncio
async def test_real_sukl_search():
    """Verify code works with live SÚKL MCP server."""
    client = SUKLMCPClient(base_url="https://sukl-mcp-ts.vercel.app/mcp")
    response = await client.call_tool("search_drugs", {"query": "Ibalgin"})

    assert response.success
    assert "drugs" in response.data
    assert len(response.data["drugs"]) > 0
    await client.close()
```

**4. No cache tests:**
```python
# Redis caching is mentioned in architecture, but no tests for:
# - Cache hit behavior
# - Cache invalidation
# - Cache key collisions
# - Redis connection failure handling
```

---

## 4. Performance Tests

### Analyzed File: `test_pubmed_latency.py`

### ✅ Strengths

**Clear performance targets:**
```python
# SC-001: p90 < 5000ms for search queries
# PMID lookups: < 3000ms
```

**Good test structure:**
```python
start_time = time.perf_counter()
await pubmed_agent_node(state, mock_runtime)
end_time = time.perf_counter()
latency_ms = (end_time - start_time) * 1000

assert latency_ms < 5000, f"Search query latency {latency_ms:.0f}ms exceeds 5s target"
```

### ⚠️ Weaknesses

**1. Tests use mocks, not real services:**
```python
# Line 13: "Note: Uses mocked backends to avoid API costs"
```

**Problem:** Mock calls complete in <1ms. Real BioMCP calls take 2-4s. These tests cannot detect real performance issues.

**2. No p90 calculation from real traces:**
```python
@pytest.mark.skip(reason="Requires actual LangSmith traces for p90 calculation")
async def test_p90_latency_from_langsmith_traces(self):
    pass
```

**Should have:**
```python
@pytest.mark.asyncio
async def test_p90_from_langsmith_production_traces():
    """Validate p90 latency from last 1000 production queries."""
    from langchain_smith import Client

    client = Client()
    runs = client.list_runs(
        project_name="czech-medai-prod",
        filter="eq(name, 'pubmed_agent_node')",
        limit=1000
    )

    latencies = [run.total_time for run in runs]
    p90 = calculate_p90_latency(latencies)

    assert p90 < 5000, f"Production p90 latency {p90:.0f}ms exceeds target"
```

**3. No load tests:**
```bash
# tests/load_tests/locustfile.py exists but appears unused
# No CI integration for load testing
# No documentation on how to run it
```

---

## 5. Missing Test Categories

### 🚨 Contract Tests (Critical Gap)

**Problem:** MCP servers can change their API without warning. No protection against:
- SÚKL changing JSON-RPC response structure
- BioMCP changing REST endpoint schemas
- Breaking changes in tool parameter requirements

**Solution: Add contract tests:**

```python
# tests/contract/test_sukl_contract.py

import pytest
from pact import Consumer, Provider, Like, EachLike

@pytest.fixture(scope="session")
def pact():
    pact = Consumer("czech-medai").has_pact_with(
        Provider("sukl-mcp-server"),
        pact_dir="pacts"
    )
    pact.start_service()
    yield pact
    pact.stop_service()

def test_search_drugs_contract(pact):
    """Verify SÚKL search_drugs contract is honored."""
    expected_response = {
        "jsonrpc": "2.0",
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": Like("Found 2 medicines...")
                }
            ]
        },
        "id": Like(1)
    }

    (pact
     .given("drugs exist for query")
     .upon_receiving("a search_drugs request")
     .with_request("POST", "/mcp")
     .will_respond_with(200, body=expected_response))

    with pact:
        client = SUKLMCPClient(base_url=pact.uri)
        response = await client.call_tool("search_drugs", {"query": "aspirin"})
        assert response.success
```

### 🚨 Smoke Tests (Critical Gap)

**Solution: Add live service smoke tests:**

```python
# tests/smoke/test_live_sukl.py

@pytest.mark.live
@pytest.mark.asyncio
async def test_sukl_mcp_server_is_reachable():
    """Verify SÚKL MCP server at https://sukl-mcp-ts.vercel.app/mcp is live."""
    client = SUKLMCPClient(base_url="https://sukl-mcp-ts.vercel.app/mcp")

    try:
        response = await client.call_tool("search_drugs", {"query": "Ibalgin", "limit": 1})
        assert response.success, f"SÚKL MCP server returned error: {response.error}"
        assert "drugs" in response.data, "SÚKL response missing 'drugs' field"
    finally:
        await client.close()

@pytest.mark.live
@pytest.mark.asyncio
async def test_sukl_response_schema_valid():
    """Verify SÚKL returns expected schema for search_drugs."""
    client = SUKLMCPClient(base_url="https://sukl-mcp-ts.vercel.app/mcp")

    try:
        response = await client.call_tool("search_drugs", {"query": "Paralen", "limit": 5})

        # Validate schema
        assert isinstance(response.data["drugs"], list)
        if response.data["drugs"]:
            drug = response.data["drugs"][0]
            assert "name" in drug
            assert "registration_number" in drug
            assert "atc_code" in drug or drug["atc_code"] is None  # Allow None
    finally:
        await client.close()
```

**Run in CI:**
```yaml
# .github/workflows/smoke-tests.yml
name: Smoke Tests (Live Services)
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
  workflow_dispatch:

jobs:
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run smoke tests
        run: |
          cd langgraph-app
          PYTHONPATH=src pytest tests/smoke/ -v -m live
```

### 🚨 Error Scenario Tests

**Missing:**
- MCP server returns 500 error
- MCP server times out (30s+)
- MCP server returns malformed JSON
- Partial failure (1 agent succeeds, 1 fails)
- Network disconnect mid-stream
- Redis connection failure
- Database connection pool exhaustion

**Solution:**

```python
# tests/integration_tests/test_error_scenarios.py

@pytest.mark.asyncio
async def test_mcp_timeout_graceful_degradation():
    """Verify graceful handling when SÚKL times out."""
    # Mock client that sleeps for 35s (exceeds 30s timeout)
    mock_client = MagicMock()
    async def slow_call(*args, **kwargs):
        await asyncio.sleep(35)
        raise MCPTimeoutError("Request timeout")

    mock_client.call_tool = AsyncMock(side_effect=slow_call)

    state = State(messages=[{"role": "user", "content": "Ibalgin"}])
    mock_runtime = MagicMock()
    mock_runtime.context = {"sukl_mcp_client": mock_client}

    result = await drug_agent_node(state, mock_runtime)

    # Should return error message, not crash
    assert "chyba" in result["messages"][0]["content"].lower()
    assert result["retrieved_docs"] == []

@pytest.mark.asyncio
async def test_partial_agent_failure_recovery():
    """Verify system continues when 1 of 2 agents fails."""
    # Compound query: drug_agent succeeds, pubmed_agent fails

    state = State(messages=[{"role": "user", "content": "Metformin - info a studie"}])

    with patch("agent.nodes.drug_agent.drug_agent_node") as mock_drug:
        with patch("agent.nodes.pubmed_agent.pubmed_agent_node") as mock_pubmed:
            # Drug agent succeeds
            mock_drug.return_value = {
                "messages": [{"role": "assistant", "content": "Metformin info [1]"}],
                "retrieved_docs": [Document(page_content="Drug doc")]
            }

            # PubMed agent fails
            mock_pubmed.side_effect = MCPTimeoutError("BioMCP timeout")

            result = await graph.ainvoke(state)

            # Should have drug_agent response + error notice for pubmed
            assert len(result["messages"]) >= 2
            # Synthesizer should note partial failure
            final_msg = result["messages"][-1]["content"]
            assert "metformin" in final_msg.lower()
            # Should mention pubmed failure
            assert "chyba" in final_msg.lower() or "nedostupn" in final_msg.lower()
```

### 🚨 SSE Streaming Tests

```python
# tests/integration_tests/test_sse_streaming.py

import httpx
import pytest

@pytest.mark.asyncio
async def test_sse_incremental_delivery():
    """Verify SSE events arrive incrementally, not buffered."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        url = "http://localhost:8000/api/v1/consult"
        request_body = {"query": "Ibalgin složení", "mode": "deep"}

        event_timestamps = []

        async with client.stream("POST", url, json=request_body) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            start = time.time()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    event_timestamps.append({
                        "elapsed": time.time() - start,
                        "type": data.get("type"),
                        "agent": data.get("agent")
                    })

        # Verify events arrive over time, not all at once
        assert event_timestamps[0]["elapsed"] < 0.5  # First event quick
        assert event_timestamps[-1]["elapsed"] > 1.0  # Last event after work done

        # Verify event sequence
        types = [e["type"] for e in event_timestamps]
        assert types[0] == "agent_start"
        assert "final" in types
        assert types[-1] == "done"

@pytest.mark.asyncio
async def test_sse_error_event_on_failure():
    """Verify error events are sent on failures."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Send query with missing required parameter
        url = "http://localhost:8000/api/v1/consult"
        request_body = {"query": "", "mode": "quick"}  # Empty query

        async with client.stream("POST", url, json=request_body) as response:
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))

        # Should have error event
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) > 0
        assert "detail" in error_events[0]
```

### 🚨 Chaos/Resilience Tests

```python
# tests/chaos/test_resilience.py

@pytest.mark.chaos
@pytest.mark.asyncio
async def test_redis_cache_failure_graceful_degradation():
    """Verify system works when Redis is down."""
    # Simulate Redis connection failure
    with patch("api.cache.get_cached_response", side_effect=ConnectionError("Redis down")):
        with patch("api.cache.set_cached_response", side_effect=ConnectionError("Redis down")):
            # Query should still work (just not cached)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/api/v1/consult",
                    json={"query": "Ibalgin", "mode": "quick"}
                )

                assert response.status_code == 200
                # Should not have cache_hit event
                # Should have final response

@pytest.mark.chaos
@pytest.mark.asyncio
async def test_database_connection_pool_exhaustion():
    """Verify system handles connection pool exhaustion."""
    # Create 20 parallel requests (exceed pool size)
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post(
                "http://localhost:8000/api/v1/consult",
                json={"query": f"Guidelines query {i}", "mode": "quick"}
            )
            for i in range(20)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Some may fail gracefully, but server should not crash
        successful = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
        assert len(successful) > 0, "At least some requests should succeed"
```

---

## 6. Test Isolation Issues

### ⚠️ Shared State Risks

**1. Module-level MCP client initialization:**
```python
# agent/graph.py (imported by tests)
_sukl_client: SUKLMCPClient | None = None
_biomcp_client: BioMCPClient | None = None

def get_mcp_clients(runtime: Runtime[Context]) -> tuple[SUKLMCPClient | None, ...]:
    global _sukl_client, _biomcp_client
    # ... lazy init with actual connections
```

**Problem:** Tests that import `graph.py` trigger real MCP client initialization unless mocked.

**Current workaround:**
```python
# tests must always do:
with patch("agent.graph.get_mcp_clients", return_value=(None, None)):
    # test code
```

**Better solution:**
```python
# Use dependency injection, not globals
@pytest.fixture(autouse=True)
def isolate_mcp_clients(monkeypatch):
    """Prevent real MCP client init in tests."""
    monkeypatch.setattr("agent.graph._sukl_client", None)
    monkeypatch.setattr("agent.graph._biomcp_client", None)
```

---

## 7. Best Practices Assessment

### ✅ Good Practices

1. **Asyncio test configuration:**
```toml
# pyproject.toml
asyncio_mode = "auto"
```
No need for `@pytest.mark.asyncio` decorators.

2. **Test naming conventions:**
```python
def test_<action>_<expected_behavior>()
def test_<component>_<scenario>()
```
Clear and descriptive.

3. **Test organization:**
- Separate unit/integration/performance directories
- Tests grouped by feature in classes
- Fixtures organized by feature in conftest.py

4. **Fixture scope management:**
```python
@pytest.fixture(scope="session")  # Expensive setup once
@pytest.fixture  # Default function scope for isolation
```

5. **Use of TYPE_CHECKING for circular imports:**
```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.graph import State, Context
```

### ⚠️ Anti-Patterns

1. **Testing implementation, not behavior:**
```python
# Bad: Testing mock calls
mock_sukl_client.call_tool.assert_called_once()
call_args = mock_sukl_client.call_tool.call_args
assert call_args[0][1]["limit"] == 5

# Better: Testing actual behavior
results = await _search_drugs(real_client, query)
assert len(results) <= 5  # Verify limit works
```

2. **Over-mocking in "integration" tests:**
```python
# test_supervisor_flow.py - not really integration
with patch("agent.nodes.supervisor.IntentClassifier"):
    with patch("agent.nodes.drug_agent.drug_agent_node"):
        result = await graph.ainvoke(...)  # Everything mocked!
```

3. **No test data builders:**
```python
# Repeated test data setup in every test
state = State(
    messages=[{"role": "user", "content": "..."}],
    next="__end__",
    retrieved_docs=[],
)

# Better: Builder pattern
state = StateBuilder().with_user_message("...").build()
```

---

## 8. Specific Recommendations

### Priority 1: Critical (Implement Immediately)

**1. Add smoke tests for live SÚKL MCP server:**
```bash
mkdir -p tests/smoke
# Create tests/smoke/test_live_sukl.py (see section 5)
```

**2. Add contract tests:**
```bash
pip install pact-python
mkdir -p tests/contract
# Create tests/contract/test_sukl_contract.py (see section 5)
```

**3. Add real SSE streaming tests:**
```python
# tests/integration_tests/test_sse_streaming.py
# Use httpx.AsyncClient().stream() instead of TestClient
```

**4. Add error scenario tests:**
```python
# tests/integration_tests/test_error_scenarios.py
# - MCP timeout
# - Malformed response
# - Partial agent failure
# - Redis failure
# - Database pool exhaustion
```

### Priority 2: High (Implement This Sprint)

**5. Add pytest markers:**
```python
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "live: tests that call live external services",
    "slow: tests that take >5s",
    "chaos: chaos engineering tests",
    "contract: contract validation tests",
]
```

**6. Create `tests/smoke/README.md`:**
```markdown
# Smoke Tests

Run against live services to validate deployment.

## Quick Start
```bash
PYTHONPATH=src pytest tests/smoke/ -v -m live
```

## CI Integration
Runs daily at 6 AM UTC via `.github/workflows/smoke-tests.yml`
```

**7. Fix mock_runtime fixture:**
```python
# tests/conftest.py
@pytest.fixture
def mock_runtime(mock_sukl_client, mock_biomcp_client):
    """Runtime with pre-wired mock clients."""
    class MockRuntime:
        def __init__(self):
            self.context = {
                "sukl_mcp_client": mock_sukl_client,
                "biomcp_client": mock_biomcp_client,
                "model_name": "test-model",
                "temperature": 0.0,
            }
    return MockRuntime()
```

### Priority 3: Medium (Next Month)

**8. Add load tests CI integration:**
```yaml
# .github/workflows/load-tests.yml
- name: Run Locust load tests
  run: |
    cd langgraph-app/tests/load_tests
    locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 60s --host http://localhost:8000
```

**9. Add test data builders:**
```python
# tests/builders.py
class StateBuilder:
    def __init__(self):
        self._messages = []
        self._next = "__end__"
        self._retrieved_docs = []

    def with_user_message(self, content: str):
        self._messages.append({"role": "user", "content": content})
        return self

    def with_drug_query(self, query_text: str):
        self._drug_query = DrugQuery(query_text=query_text, query_type=QueryType.SEARCH)
        return self

    def build(self) -> State:
        return State(
            messages=self._messages,
            next=self._next,
            retrieved_docs=self._retrieved_docs,
            drug_query=getattr(self, "_drug_query", None),
        )
```

**10. Add mutation testing:**
```bash
pip install mutmut
mutmut run --paths-to-mutate src/agent/nodes/
```

### Priority 4: Low (Future)

**11. Add visual regression tests for citations:**
```python
# Verify citation rendering in frontend
# Use Playwright + Percy for screenshot diffs
```

**12. Add property-based tests:**
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
def test_drug_query_classification_never_crashes(query_text):
    """Fuzz test query classification with random inputs."""
    result = classify_drug_query(query_text)
    assert result in QueryType.__members__.values()
```

---

## 9. Metrics Recommendations

### Current State
- **Test Count:** 539 test functions
- **Test Code:** ~11,384 lines
- **Coverage:** Unknown (no coverage reports found)
- **Live Tests:** 0
- **Contract Tests:** 0

### Target Metrics

| Metric | Current | Target | Priority |
|--------|---------|--------|----------|
| Unit test coverage | Unknown | ≥90% | High |
| Live service tests | 0 | ≥5 | Critical |
| Contract tests | 0 | 1 per MCP server | Critical |
| SSE streaming tests | 0 | ≥3 | Critical |
| Error scenario tests | ~3 | ≥15 | High |
| Chaos tests | 0 | ≥5 | Medium |
| Performance tests (real) | 0 | ≥3 | High |
| Mutation score | Unknown | ≥80% | Low |

### Add Coverage Reporting

```bash
# pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "src/api/main.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

```bash
# Run with coverage
PYTHONPATH=src pytest tests/ --cov=src --cov-report=html --cov-report=term
```

---

## 10. Summary: What's Good vs. What's Missing

### ✅ What's Good

1. **Solid unit test foundation** - 442 passing tests with good organization
2. **Well-structured fixtures** - Feature-based organization in conftest.py
3. **Good LangGraph test patterns** - Send API, State, Runtime properly tested
4. **TDD evidence** - Clear test-first development in some modules
5. **Async test setup** - Proper asyncio_mode configuration
6. **Edge case coverage in units** - Empty inputs, errors, validation

### 🚨 Critical Gaps

1. **Zero live service tests** - No validation against real SÚKL MCP (which is live!)
2. **No contract tests** - MCP server API changes undetected
3. **No real SSE streaming tests** - TestClient buffers, not true streaming
4. **Minimal error scenarios** - Timeouts, malformed responses, partial failures
5. **No chaos/resilience tests** - Unknown behavior under degraded conditions
6. **Performance tests use mocks** - Cannot detect real latency issues
7. **No load testing in CI** - Locustfile exists but unused

### 🔧 Specific Tests to Add (Next Sprint)

```python
# tests/smoke/test_live_sukl.py
@pytest.mark.live
async def test_sukl_mcp_server_is_reachable()

# tests/contract/test_sukl_contract.py
def test_search_drugs_contract(pact)

# tests/integration_tests/test_sse_streaming.py
@pytest.mark.asyncio
async def test_sse_incremental_delivery()

# tests/integration_tests/test_error_scenarios.py
@pytest.mark.asyncio
async def test_mcp_timeout_graceful_degradation()
async def test_partial_agent_failure_recovery()
async def test_malformed_mcp_response_handling()

# tests/chaos/test_resilience.py
@pytest.mark.chaos
async def test_redis_cache_failure_graceful_degradation()
async def test_database_connection_pool_exhaustion()
```

---

## Conclusion

Czech MedAI má velmi dobrý základ unit testů, ale **kriticky postrádá testy, které validují skutečné chování systému**. Všechny testy používají mocky, což znamená:

- ✅ Rychlé, deterministické testy
- ✅ Dobrá izolace komponent
- ❌ **Žádná validace, že kód funguje s reálnými službami**
- ❌ **Žádná ochrana před breaking changes v MCP serverech**
- ❌ **Nerealistické výkonnostní testy**

**Doporučení:** Přidejte smoke tests, contract tests a real SSE tests jako prioritu 1. Systém má live SÚKL MCP server na `https://sukl-mcp-ts.vercel.app/mcp` - využijte ho!

---

**Audit Completed:** 2026-02-16
**Next Review:** After implementing Priority 1 recommendations
