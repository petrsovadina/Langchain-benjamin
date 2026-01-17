# Implementation Plan: SÚKL Drug Agent

**Branch**: `003-sukl-drug-agent` | **Date**: 2026-01-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-sukl-drug-agent/spec.md`

## Summary

Implementace LangGraph node `drug_agent_node` pro vyhledávání a získávání informací o lécích z české farmaceutické databáze SÚKL. Node využívá existující `SUKLMCPClient` z Feature 002 (MCP Infrastructure) a poskytuje strukturované odpovědi s citacemi.

Technický přístup: Vytvoření async node funkce s integrací na 8 SÚKL-mcp tools, rozšíření State o `drug_query` pole, přidání Pydantic modelů pro validaci vstupů/výstupů.

## Technical Context

**Language/Version**: Python ≥3.10 (per constitution)
**Primary Framework**: LangGraph ≥1.0.0 (per constitution)
**Additional Dependencies**:
- `pydantic ≥2.0` (již nainstalován v Feature 002)
- `agent.mcp.SUKLMCPClient` (Feature 002)
- `langchain_core.documents.Document` (pro citace)

**Storage**: LangGraph checkpointing (per constitution - no direct ORM)
**Testing**: pytest s aiohttp mocking (per constitution)
**Target Platform**: LangGraph Server via `langgraph dev`
**Project Type**: LangGraph Agent (rozšíření grafu v `src/agent/graph.py`)
**Performance Goals**: <3s vyhledávání léku, <5s detailní informace
**Constraints**: Async-first (per constitution), využití existující MCP infrastruktury
**Scale/Scope**: 1 nový node, 5 Pydantic modelů, rozšíření State o 1 pole

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Graph-Centric Architecture
- [x] Feature designed as LangGraph node (`drug_agent_node`) in `src/agent/graph.py`
- [x] Node follows async signature: `async def drug_agent_node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- [x] State transitions explicit via `.add_edge()` - node vrací `next` field
- [x] Graph structure visualizable in LangGraph Studio - jeden node s jasným vstupem/výstupem

### Principle II: Type Safety & Schema Validation
- [x] `State` dataclass rozšířen o `drug_query: Optional[DrugQuery]` pole
- [x] `Context` TypedDict již obsahuje `sukl_mcp_client` (Feature 002)
- [x] Všechny vstupy/výstupy node typovány (Pydantic models)
- [x] Pydantic models pro externí data: DrugQuery, DrugResult, DrugDetails, ReimbursementInfo

### Principle III: Test-First Development
- [x] Unit testy plánované v `tests/unit_tests/nodes/test_drug_agent.py`
- [x] Integration testy v `tests/integration_tests/test_drug_agent_flow.py`
- [x] Test-first workflow: napsat test → fail → implement → pass

### Principle IV: Observability & Debugging
- [x] LangSmith tracing enabled (LANGSMITH_API_KEY in .env)
- [x] Logging na začátku a konci node execution
- [x] State transitions logovány (drug_query → drug_results)
- [x] Testing zahrnuje LangGraph Studio verification

### Principle V: Modular & Extensible Design
- [x] `drug_agent_node` má jedinou zodpovědnost: zpracování drug queries
- [x] Helper funkce extrahované do `src/agent/nodes/drug_agent.py`
- [x] Konfigurace (timeout, retry) v Context, ne hardcoded
- [x] Subgraphs zatím nepotřeba - jednoduchý node pattern

## Project Structure

### Documentation (this feature)

```text
specs/003-sukl-drug-agent/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── drug_agent.yaml  # Node contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
langgraph-app/
├── src/
│   └── agent/
│       ├── graph.py              # Main graph - ADD drug_agent_node
│       ├── nodes/                # NEW directory
│       │   ├── __init__.py
│       │   └── drug_agent.py     # Drug agent implementation
│       ├── models/               # NEW directory
│       │   ├── __init__.py
│       │   └── drug_models.py    # Pydantic models
│       ├── mcp/                  # Existing from Feature 002
│       │   └── adapters/sukl_client.py
│       └── __init__.py
├── tests/
│   ├── unit_tests/
│   │   └── nodes/               # NEW directory
│   │       ├── __init__.py
│   │       └── test_drug_agent.py
│   ├── integration_tests/
│   │   └── test_drug_agent_flow.py  # NEW
│   └── conftest.py              # ADD drug agent fixtures
├── pyproject.toml
├── langgraph.json
└── README.md
```

**Structure Decision**: Rozšíření existující LangGraph struktury s novými `nodes/` a `models/` adresáři pro modulární organizaci. Zachována stávající MCP infrastruktura.

## Node Design

### drug_agent_node

```python
async def drug_agent_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Process drug-related queries using SÚKL MCP.

    Workflow:
    1. Extract drug query from state.drug_query or parse from last message
    2. Determine query type (search, details, reimbursement, availability)
    3. Call appropriate SUKLMCPClient method
    4. Transform response to Documents with citations
    5. Return updated state with retrieved_docs
    """
```

### State Extension

```python
@dataclass
class State:
    messages: Annotated[list[AnyMessage], add_messages]
    next: str = "__end__"
    retrieved_docs: list[Document] = field(default_factory=list)
    # NEW: Drug query field
    drug_query: Optional[DrugQuery] = None
```

## Complexity Tracking

> Žádné porušení Constitution - plán dodržuje všechny principy.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |

## Dependencies

### Internal Dependencies
- **Feature 002**: MCP Infrastructure (SUKLMCPClient, MCPConfig, RetryConfig) - COMPLETE

### External Dependencies
- **SÚKL-mcp server**: https://github.com/petrsovadina/SUKL-mcp
  - 8 MCP tools pro přístup k databázi 68k+ léků
  - Fuzzy matching s rapidfuzz (threshold 80%)
  - CSV fallback pro offline mode

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| SÚKL server nedostupný | Medium | High | Retry strategy + graceful error messages |
| Timeout při velkých queries | Low | Medium | Configurable timeout, limit results |
| Fuzzy matching nesprávné výsledky | Low | Low | Threshold 80% + zobrazení score |
