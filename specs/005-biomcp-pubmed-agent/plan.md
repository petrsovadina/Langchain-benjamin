# Implementation Plan: BioMCP PubMed Agent

**Branch**: `005-biomcp-pubmed-agent` | **Date**: 2026-01-20 | **Spec**: [spec.md](./spec.md)

## Summary

Implement PubMed research agent with Czech ↔ English translation using BioMCP for international biomedical literature search. Primary requirement: Physicians can search PubMed with Czech queries and receive translated results with full citation tracking. Technical approach: LLM-based translation (Claude Sonnet 4.5) via dedicated graph nodes, BioMCP client integration (Feature 002), LangChain Document format for citations.

## Technical Context

**Language/Version**: Python ≥3.10 (per constitution)
**Primary Framework**: LangGraph ≥1.0.0 (per constitution)
**Additional Dependencies**: biomcp-python (BioMCP client), existing langchain, anthropic
**Storage**: LangGraph checkpointing (per constitution - no direct ORM)
**Testing**: pytest with async support (per constitution)
**Target Platform**: LangGraph Server via `langgraph dev`
**Project Type**: LangGraph Agent (single graph in `src/agent/graph.py`)
**Performance Goals**: <5s full flow for 90% queries (SC-001), $0.001 per query
**Constraints**: Async-first (per constitution), minimal external deps (LLM-based translation, no external APIs)
**Scale/Scope**: 3 new nodes (translate_cz_to_en, translate_en_to_cz, pubmed_agent), State schema +1 field (research_query), default 5 articles per query

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Graph-Centric Architecture
- [x] Feature designed as LangGraph nodes/edges in `src/agent/graph.py`
- [x] All nodes follow async signature: `async def node_name(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- [x] State transitions explicit via `.add_edge()` (pubmed_agent → __end__)
- [x] Graph structure visualizable in LangGraph Studio (3 new nodes)

### Principle II: Type Safety & Schema Validation
- [x] `State` dataclass updated with `research_query: Optional[ResearchQuery]` field
- [x] `Context` TypedDict already supports biomcp_client (Feature 002 MCP infrastructure)
- [x] All node inputs/outputs typed correctly (Dict[str, Any] return type)
- [x] Pydantic models for external data: ResearchQuery, PubMedArticle, TranslatedArticle, CitationReference

### Principle III: Test-First Development
- [x] Unit tests planned: `tests/unit_tests/nodes/test_translation.py` (12 tests), `test_pubmed_agent.py` (15 tests)
- [x] Integration tests planned: `tests/integration_tests/test_pubmed_agent_flow.py` (8 tests)
- [x] Test-first workflow confirmed: Write test → Fail → Implement → Pass

### Principle IV: Observability & Debugging
- [x] LangSmith tracing enabled (LANGSMITH_API_KEY in .env)
- [x] Logging at node boundaries (query classification, BioMCP calls, translations)
- [x] State transitions logged (research_query populated, retrieved_docs count)
- [x] Testing plan includes LangGraph Studio verification (graph visualization)

### Principle V: Modular & Extensible Design
- [x] Nodes are small and single-responsibility (translate_cz_to_en, translate_en_to_cz, pubmed_agent)
- [x] Reusable logic extracted to helpers (classify_research_query, article_to_document, format_citation)
- [x] Configuration parameters use Context (max_results, translation_enabled, batch_size)
- [x] No subgraphs needed (3 nodes sufficient for MVP)

**GATE STATUS**: ✅ PASSED - All constitutional principles satisfied

## Project Structure

### Documentation (this feature)

```text
specs/005-biomcp-pubmed-agent/
├── spec.md                   # Feature specification (3 user stories, 11 FRs)
├── plan.md                   # This file
├── research.md               # Phase 0: Translation strategy + BioMCP integration decisions
├── data-model.md             # Phase 1: ResearchQuery, PubMedArticle, Citation entities
├── quickstart.md             # Phase 1: Developer setup guide
├── contracts/                # Phase 1: Node contracts
│   └── pubmed_agent.yaml     # Input/output schemas for all nodes
└── tasks.md                  # Phase 2: NOT created yet (/speckit.tasks command)
```

### Source Code (repository root)

```text
langgraph-app/
├── src/
│   └── agent/
│       ├── graph.py                           # Main graph + route_query() extension
│       ├── models/
│       │   ├── drug_models.py                 # Feature 003
│       │   └── research_models.py             # ← NEW: ResearchQuery, PubMedArticle, etc.
│       ├── nodes/
│       │   ├── drug_agent.py                  # Feature 003
│       │   ├── translation.py                 # ← NEW: translate_cz_to_en, translate_en_to_cz
│       │   └── pubmed_agent.py                # ← NEW: pubmed_agent_node + helpers
│       ├── utils/
│       │   └── translation_prompts.py         # ← NEW: CZ_TO_EN_PROMPT, EN_TO_CZ_PROMPT
│       └── mcp/
│           └── adapters/
│               └── biomcp_client.py           # Feature 002 (reused)
├── tests/
│   ├── unit_tests/
│   │   ├── nodes/
│   │   │   ├── test_drug_agent.py            # Feature 003
│   │   │   ├── test_translation.py           # ← NEW: 12 translation tests
│   │   │   └── test_pubmed_agent.py          # ← NEW: 15 pubmed_agent tests
│   │   └── mcp/
│   │       └── test_biomcp_client.py         # Feature 002 (reused)
│   ├── integration_tests/
│   │   ├── test_drug_agent_flow.py           # Feature 003
│   │   └── test_pubmed_agent_flow.py         # ← NEW: 8 integration tests
│   └── conftest.py                           # Pytest fixtures (extend with BioMCP mocks)
├── pyproject.toml                            # Add biomcp-python dependency
└── langgraph.json                            # LangGraph server config (no changes)
```

## Architecture Overview

### Graph Flow

```
User Query (Czech): "Jaké jsou studie o diabetu typu 2?"
    ↓
[route_query] ← Keyword detection: "studie" → pubmed_agent
    ↓
[translate_cz_to_en_node]
    │ Input: Czech query
    │ Output: English query for PubMed
    │ Latency: ~1-2s (LLM call, temperature=0)
    ↓
[pubmed_agent_node]
    │ Calls: BioMCPClient.search_articles(english_query)
    │ Returns: List[PubMedArticle] (English metadata + abstracts)
    │ Latency: ~2-3s (PubMed API via BioMCP)
    ↓
[translate_en_to_cz_node]
    │ Input: List[PubMedArticle] with English abstracts
    │ Output: List[Document] with Czech abstracts
    │ Latency: ~1-2s (parallel LLM calls, batch_size=5)
    ↓
[retrieved_docs] populated with 5 Documents
    ↓
[__end__] (Future: → citation_system → synthesizer)
    ↓
Response (Czech) with inline citations [1][2][3][4][5]
```

### Routing Keywords

Extend `route_query()` in graph.py:

```python
RESEARCH_KEYWORDS = {
    "studie", "výzkum", "pubmed", "článek", "literatura",
    "pmid", "výzkumný", "klinická studie"
}

def route_query(state: State) -> Literal["drug_agent", "pubmed_agent", "placeholder"]:
    # Priority: drug_agent > pubmed_agent > placeholder
    if state.drug_query is not None:
        return "drug_agent"

    if state.research_query is not None:
        return "pubmed_agent"

    # Check keywords
    content_lower = get_last_message_content(state).lower()
    for keyword in DRUG_KEYWORDS:
        if keyword in content_lower:
            return "drug_agent"
    for keyword in RESEARCH_KEYWORDS:
        if keyword in content_lower:
            return "pubmed_agent"

    return "placeholder"
```

## Key Implementation Decisions

*(From research.md - summarized)*

### Decision 1: Translation Strategy
- **Choice**: LLM-based (Claude Sonnet 4.5) via dedicated nodes
- **Rationale**: Zero external dependencies, superior medical terminology handling, $0.90/month for 1000 queries
- **Rejected**: DeepL API ($5.99/month, external dependency), Hybrid glossary (over-engineering for MVP)

### Decision 2: BioMCP Integration
- **Choice**: Reuse existing BioMCPClient from Feature 002
- **Implementation**: Access via `runtime.context.get("biomcp_client")`
- **Tools Used**: `article_searcher` (PubMed search), `article_getter` (PMID lookup)

### Decision 3: State Schema
- **Extension**: Add `research_query: Optional[ResearchQuery]` to State dataclass
- **Pattern**: Parallel to `drug_query` from Feature 003
- **Routing**: Enables keyword-based routing (MVP) → LLM supervisor (Feature 007)

### Decision 4: Citation Tracking
- **Format**: LangChain Documents with metadata.source="PubMed"
- **Helper**: `article_to_document(article, czech_abstract) -> Document`
- **URL**: Every Document includes PubMed URL (SC-004: 100% auditable)

## Performance Targets

| Metric | Target | Implementation |
|--------|--------|----------------|
| **SC-001: Latency** | <5s (90% queries) | Parallel abstract translation (batch_size=5), LRU cache |
| **SC-002: Translation Quality** | 95% semantic preservation | Medical-specialized prompts, temperature=0 |
| **SC-003: First-Search Success** | 80% find relevant article | BioMCP relevance ranking + top 5 results |
| **SC-004: Auditability** | 100% PubMed URLs | metadata.url in every Document |
| **SC-005: Graceful Failures** | Czech error messages | Try-except with BioMCP timeout/connection handling |

**Cost**: $0.001 per query (1800 tokens avg) → $1/month for 1000 queries

## Dependencies & Integration Points

| Dependency | Status | Integration |
|------------|--------|-------------|
| **Feature 002: MCP Infrastructure** | ✅ Complete | BioMCPClient already implemented |
| **Feature 003: Drug Agent** | ✅ Complete | Routing pattern, State schema precedent |
| **BioMCP Server** | External | Docker container on localhost:8080 |
| **Claude Sonnet 4.5** | Runtime | Translation via LLM calls (temperature=0) |
| **LangChain Documents** | Core | Citation format for Feature 008 compatibility |

## Testing Strategy

### Unit Tests (27 total)

**test_translation.py (12 tests)**:
- translate_cz_to_en_basic
- translate_preserves_medical_terms
- translate_expands_abbreviations
- translate_empty_messages_error
- translate_en_to_cz_multiple_docs
- translate_preserves_metadata
- (6 more for edge cases)

**test_pubmed_agent.py (15 tests)**:
- pubmed_search_returns_documents
- pubmed_handles_no_results
- pubmed_formats_citations_correctly
- pubmed_pmid_lookup
- pubmed_biomcp_timeout_fallback
- (10 more for query classification, document transformation)

### Integration Tests (8 total)

**test_pubmed_agent_flow.py**:
- test_full_cz_en_cz_translation_flow
- test_pubmed_search_with_date_filter
- test_pmid_lookup_flow
- test_citation_tracking_across_queries
- test_biomcp_failure_graceful_degradation
- (3 more for edge cases)

### Performance Benchmarks

**test_translation_latency.py**:
- test_translation_under_2_seconds
- test_full_pubmed_flow_under_5_seconds
- test_parallel_abstract_translation_speedup

### Manual Validation

- **Bilingual Medical Expert Review** (20 sample queries)
- **LangGraph Studio Visual Inspection** (graph flow correctness)
- **LangSmith Trace Analysis** (latency breakdown, token usage)

## Phase Summary

### Phase 0: Research (COMPLETE ✅)
- Translation strategy validated (LLM-based, Claude Sonnet 4.5)
- BioMCP integration pattern confirmed (existing client)
- Performance targets validated (4-7s latency, $0.90/month)
- All unknowns resolved (no NEEDS CLARIFICATION remaining)

### Phase 1: Design (COMPLETE ✅)
- Data model defined: ResearchQuery, PubMedArticle, TranslatedArticle, CitationReference
- Node contracts specified: pubmed_agent.yaml with input/output schemas
- Quickstart guide created: 8-10 hour implementation estimate
- Agent context NOT updated (no new technologies - reuses existing LangGraph + BioMCP)

### Phase 2: Tasks (NEXT STEP)
- Run `/speckit.tasks` to generate tasks.md
- Expected: ~50-60 atomic tasks across 8 phases (Setup, US1-US3, Integration, Polish)
- Pattern: Similar to Feature 003 (58 tasks)

## Next Steps

1. **Approve Plan** - Review this document for completeness
2. **Run /speckit.tasks** - Generate task breakdown
3. **Run /speckit.implement** - Execute tasks with test-first approach
4. **LangGraph Studio Verification** - Test graph visualization
5. **Create Pull Request** - Merge to main after review

**Ready for**: Task generation phase
**Estimated Implementation**: 8-10 hours (with TDD)
