# Quick Start: BioMCP PubMed Agent

**Feature**: 005-biomcp-pubmed-agent
**Branch**: `005-biomcp-pubmed-agent`
**Prerequisites**: Features 001, 002 complete

---

## Setup (5 minutes)

### 1. Install BioMCP

```bash
# Install BioMCP Python package
cd langgraph-app
uv pip install biomcp-python

# Or with pip
pip install biomcp-python
```

### 2. Start BioMCP Server (Docker)

```bash
# Pull and run BioMCP container
docker run -d -p 8080:8080 --name biomcp genomoncology/biomcp:latest

# Verify server is running
curl http://localhost:8080/health
# Expected: {"status": "ok"}
```

**Alternative (Local Development)**:
```bash
# Run BioMCP via uv (no Docker)
uv run --with biomcp-python biomcp run

# Server starts on http://localhost:8080
```

### 3. Configure Environment

```bash
# Ensure .env has BioMCP configuration
echo "BIOMCP_URL=http://localhost:8080" >> langgraph-app/.env
```

---

## Implementation Checklist

### Phase 1: Data Models (1 hour)

- [ ] Create `langgraph-app/src/agent/models/research_models.py`
- [ ] Define `ResearchQuery` Pydantic model
- [ ] Define `PubMedArticle` Pydantic model
- [ ] Define `TranslatedArticle` Pydantic model (inherits PubMedArticle)
- [ ] Define `CitationReference` Pydantic model

**Verification**:
```bash
cd langgraph-app
python -c "from agent.models.research_models import ResearchQuery; print('✅ Models imported')"
```

### Phase 2: State Schema Extension (15 minutes)

- [ ] Update `langgraph-app/src/agent/graph.py`
- [ ] Add `from agent.models.research_models import ResearchQuery`
- [ ] Add `research_query: Optional[ResearchQuery] = None` to State dataclass

**Verification**:
```bash
python -c "from agent.graph import State; assert hasattr(State, 'research_query'); print('✅ State extended')"
```

### Phase 3: Translation Nodes (2 hours)

- [ ] Create `langgraph-app/src/agent/nodes/translation.py`
- [ ] Implement `translate_cz_to_en_node(state, runtime) -> Dict[str, Any]`
- [ ] Implement `translate_en_to_cz_node(state, runtime) -> Dict[str, Any]`
- [ ] Create `langgraph-app/src/agent/utils/translation_prompts.py`
- [ ] Define `CZ_TO_EN_PROMPT` template
- [ ] Define `EN_TO_CZ_PROMPT` template

**Verification**:
```bash
pytest tests/unit_tests/nodes/test_translation.py -v
# Expected: 12 tests passing
```

### Phase 4: PubMed Agent Node (3 hours)

- [ ] Create `langgraph-app/src/agent/nodes/pubmed_agent.py`
- [ ] Implement `pubmed_agent_node(state, runtime) -> Dict[str, Any]`
- [ ] Implement helper `classify_research_query(message: str) -> ResearchQuery | None`
- [ ] Implement helper `article_to_document(article, czech_abstract) -> Document`
- [ ] Implement helper `format_citation(article, citation_num) -> CitationReference`

**Verification**:
```bash
pytest tests/unit_tests/nodes/test_pubmed_agent.py -v
# Expected: 15 tests passing
```

### Phase 5: Graph Integration (30 minutes)

- [ ] Update `langgraph-app/src/agent/graph.py`
- [ ] Import `pubmed_agent_node` from `agent.nodes`
- [ ] Add `RESEARCH_KEYWORDS` set (studie, výzkum, pubmed, článek)
- [ ] Extend `route_query()` function with research keyword detection
- [ ] Add node to graph: `.add_node("pubmed_agent", pubmed_agent_node)`
- [ ] Add routing edge: `"pubmed_agent": "pubmed_agent"` in conditional_edges
- [ ] Add end edge: `.add_edge("pubmed_agent", "__end__")`

**Verification**:
```bash
python -c "from agent.graph import graph; assert 'pubmed_agent' in graph.nodes; print('✅ Graph integrated')"
```

### Phase 6: Integration Tests (1 hour)

- [ ] Create `langgraph-app/tests/integration_tests/test_pubmed_agent_flow.py`
- [ ] Test full CZ→EN→PubMed→EN→CZ flow
- [ ] Test PMID lookup flow
- [ ] Test citation tracking
- [ ] Test BioMCP failure graceful degradation

**Verification**:
```bash
pytest tests/integration_tests/test_pubmed_agent_flow.py -v
# Expected: 8 tests passing
```

---

## Testing the Feature

### Manual Test (CLI)

```bash
# Start LangGraph dev server
cd langgraph-app
langgraph dev

# Server runs on http://localhost:2024
# Open LangGraph Studio: https://smith.langchain.com/studio/?baseUrl=http://localhost:2024
```

**Test Query 1 - Basic Search**:
```
Input: "Jaké jsou nejnovější studie o diabetu typu 2?"
Expected Output:
- 5 PubMed articles with Czech abstracts
- Each article has inline citation [1], [2], [3], [4], [5]
- References section with PubMed URLs
```

**Test Query 2 - PMID Lookup**:
```
Input: "Ukaž mi článek PMID:12345678"
Expected Output:
- Single article with full details
- Czech abstract translation
- PubMed URL for verification
```

**Test Query 3 - Date Filter**:
```
Input: "Studie za poslední 2 roky o hypertenzi"
Expected Output:
- Articles from 2024-2026 only
- Date filter detected and applied
- Results filtered by publication date
```

### Automated Test Suite

```bash
# Run all Feature 005 tests
cd langgraph-app
pytest tests/unit_tests/nodes/test_translation.py tests/unit_tests/nodes/test_pubmed_agent.py tests/integration_tests/test_pubmed_agent_flow.py -v

# Expected results:
# - 12 translation tests ✅
# - 15 pubmed_agent tests ✅
# - 8 integration tests ✅
# Total: 35 tests passing
```

---

## Example Usage (Python)

```python
from agent.graph import graph, State, Context
from agent.mcp import BioMCPClient, MCPConfig

# Initialize MCP clients
config = MCPConfig.from_env()
biomcp_client = BioMCPClient(base_url=config.biomcp_url)

# Create runtime context
context: Context = {
    "model_name": "claude-sonnet-4-5",
    "temperature": 0.0,
    "biomcp_client": biomcp_client,
    "max_results": 5,
    "translation_enabled": True
}

# Create initial state
initial_state = State(
    messages=[{"role": "user", "content": "Jaké jsou nejnovější studie o diabetu typu 2?"}],
    next="",
    retrieved_docs=[],
    research_query=None
)

# Run graph
result = await graph.ainvoke(initial_state, context)

# Access results
print(f"Retrieved {len(result['retrieved_docs'])} articles")
for i, doc in enumerate(result['retrieved_docs'], 1):
    print(f"[{i}] {doc.metadata['title']}")
    print(f"    PMID: {doc.metadata['pmid']}")
    print(f"    URL: {doc.metadata['url']}")
```

---

## Performance Benchmarks

### Expected Latency (SC-001 Target: <5s)

| Step | Target | Measurement |
|------|--------|-------------|
| Query classification | <100ms | Keyword matching |
| Translation CZ→EN | 1-2s | LLM call (temperature=0) |
| BioMCP search | 2-3s | PubMed API via BioMCP |
| Translation EN→CZ (5 abstracts) | 1-2s | Parallel LLM calls (batch_size=5) |
| Document transformation | <100ms | Python processing |
| **Total** | **4-7s** | **Within target for 90% queries** |

### Expected Cost (SC-002 Target: <$1/month)

| Operation | Tokens | Cost per Query | 1000 Queries/Month |
|-----------|--------|----------------|--------------------|
| CZ→EN translation | ~300 | $0.0003 | $0.30 |
| EN→CZ translation (5 abstracts) | ~1500 | $0.0007 | $0.70 |
| **Total** | **~1800** | **$0.001** | **$1.00** |

---

## Troubleshooting

### Issue 1: BioMCP Server Not Responding

**Symptoms**:
```
MCPConnectionError: Failed to connect to BioMCP at http://localhost:8080
```

**Solution**:
```bash
# Check if Docker container is running
docker ps | grep biomcp

# Restart container if needed
docker restart biomcp

# Or start fresh container
docker run -d -p 8080:8080 --name biomcp genomoncology/biomcp:latest

# Verify health
curl http://localhost:8080/health
```

### Issue 2: Translation Quality Issues

**Symptoms**:
- Medical terms incorrectly translated
- Abbreviations not expanded
- Awkward Czech phrasing

**Solution**:
```bash
# Review translation prompts
cat langgraph-app/src/agent/utils/translation_prompts.py

# Adjust prompt templates:
# - Add more medical term examples
# - Refine abbreviation expansion rules
# - Add context-specific instructions
```

### Issue 3: Slow Performance (>5s)

**Symptoms**:
```
Performance warning: Query took 8.2s (target: <5s)
```

**Solution**:
```python
# Enable LRU cache for common queries
from functools import lru_cache

@lru_cache(maxsize=100)
def translate_cached(query: str, direction: str) -> str:
    # Cache translations for repeated queries
    pass

# Increase parallel batch size for abstracts
context["batch_size"] = 10  # Default: 5
```

### Issue 4: PMID Not Found

**Symptoms**:
```
"Article PMID:12345678 not found in PubMed database"
```

**Solution**:
- Verify PMID is valid 8-digit number
- Check article is indexed in PubMed (not just PMC)
- Try alternative search by title or DOI

---

## Next Steps

After completing Feature 005:

1. **Test in LangGraph Studio** - Verify graph visualization shows pubmed_agent node
2. **Run Full Test Suite** - Ensure all 35 tests passing
3. **Manual Quality Check** - Test with 20 sample queries (bilingual medical expert)
4. **Performance Profiling** - Verify <5s latency for 90% queries
5. **Create Pull Request** - Merge to main after review

**Ready for**: Feature 006 (Guidelines Agent) or Feature 007 (Supervisor Orchestration)

---

## Reference Files

- **Spec**: `specs/005-biomcp-pubmed-agent/spec.md`
- **Research**: `specs/005-biomcp-pubmed-agent/research.md`
- **Data Model**: `specs/005-biomcp-pubmed-agent/data-model.md`
- **Contracts**: `specs/005-biomcp-pubmed-agent/contracts/pubmed_agent.yaml`
- **Constitution**: `.specify/memory/constitution.md`

**Estimated Total Time**: 8-10 hours (with test-first approach)
