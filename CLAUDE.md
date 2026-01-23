# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Czech MedAI (Benjamin)** je multi-agentní AI asistent pro české lékaře, postavený na LangGraph frameworku. Systém poskytuje klinickou rozhodovací podporu založenou na důkazech, integrující specializované AI agenty pro dotazování českých medicínských zdrojů (SÚKL, VZP, ČLS JEP) a mezinárodního výzkumu (PubMed) s kompletním sledováním citací.

**Současný stav**: Fáze 1 (Core Agents) - Větev `005-biomcp-pubmed-agent`
- ✅ Feature 001: LangGraph Foundation (dokončeno)
- ✅ Feature 002: MCP Infrastructure (dokončeno)
- ✅ Feature 003: SÚKL Drug Agent (dokončeno)
- ✅ Feature 005: BioMCP PubMed Agent (dokončeno - včetně Phase 7 Polish)
- ⏳ Feature 004: VZP Pricing Agent (čeká)

## Technologie

- **Framework**: LangGraph ≥1.0.0 (multi-agent orchestrace)
- **Jazyk**: Python ≥3.10 (async-first architektura)
- **MCP Servery**:
  - **SÚKL-mcp** - Czech pharmaceutical database (68k+ léků)
  - **BioMCP** - Biomedical databases (PubMed, ClinicalTrials, atd.)
- **Testing**: pytest s async podporou (169/175 testů passing)
- **Kvalita kódu**: ruff (linting/formátování), mypy --strict (type checking)
- **Observability**: LangSmith tracing

## Struktura Projektu

```
langgraph-app/              # Hlavní aplikace (Python balíček)
├── src/agent/
│   ├── __init__.py        # Export balíčku
│   ├── graph.py           # Definice grafu (routing, state, context)
│   ├── mcp/               # MCP client wrappers (SÚKL, BioMCP)
│   ├── models/            # Pydantic models (drug_models, research_models)
│   ├── nodes/             # Node implementace (drug_agent, pubmed_agent, translation)
│   └── utils/             # Helper funkce (translation prompts)
├── tests/
│   ├── conftest.py        # pytest fixtures (anyio_backend, mock_runtime, samples)
│   ├── unit_tests/        # Unit testy pro nody (169 passing)
│   ├── integration_tests/ # Integrační testy pro graf
│   └── performance/       # Performance benchmarky (<5s latency)
├── pyproject.toml         # Závislosti & konfigurace nástrojů
├── Makefile               # Vývojové příkazy
└── langgraph.json         # LangGraph server konfigurace

specs/                     # Specifikace features
├── 001-langgraph-foundation/
├── 002-mcp-infrastructure/
├── 003-sukl-drug-agent/
├── 005-biomcp-pubmed-agent/
│   ├── spec.md           # User stories, požadavky
│   ├── plan.md           # Implementační plán
│   ├── tasks.md          # Rozpad úkolů (81 tasks, all complete)
│   └── contracts/        # API contracts, data models
└── ROADMAP.md            # Master roadmap (12 features, 4 fáze)

.specify/                  # SpecKit framework
├── memory/
│   └── constitution.md   # Constitution projektu v1.0.3 (5 principů)
└── templates/            # Šablony pro spec/plan/tasks
```

## Constitution Projektu

Projekt je řízen 5 základními principy v `.specify/memory/constitution.md` (verze **1.0.3**):

### I. Graph-Centric Architecture
- **VŠECHNY** features MUSÍ být implementovány jako LangGraph nody a hrany
- Node funkce MUSÍ být async: `async def node_name(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- State transitions MUSÍ být explicitní přes `.add_edge()` nebo conditional edges
- Graf MUSÍ být vizualizovatelný v LangGraph Studio

### II. Type Safety & Schema Validation
- **VŠE** state a context MUSÍ používat typed dataclasses/TypedDict
- `State` definuje všechna pole grafu s type hints
- `Context` TypedDict definuje runtime konfigurační parametry
- **mypy --strict**: Zero errors required
- **Exception**: Use `Any` with doc comment pro MCP clients (Pydantic schema compatibility)

### III. Test-First Development (NEPORUŠITELNÉ)
- **Testy MUSÍ být napsány PŘED implementací**
- Unit testy v `tests/unit_tests/`
- Integrační testy v `tests/integration_tests/`
- Workflow: Napsat test → Fail → Implementovat → Pass
- Cílové pokrytí: ≥80% (aktuálně 96%)

### IV. Observability & Debugging
- **VŠECHNY** graph executions MUSÍ být sledovatelné
- LangSmith tracing přes `.env` (`LANGSMITH_API_KEY`)
- Logování state transitions (print() povoleno pro debugging - T201)
- Použití LangGraph Studio pro vizuální debugging

### V. Modular & Extensible Design
- Každý node MUSÍ mít jednu jasnou zodpovědnost
- Preference vícero malých nodů než jeden velký
- Konfigurace v `Context`, ne hardcoded

## Běžné Příkazy

### Setup

```bash
# Instalace závislostí s uv (doporučeno)
uv pip install -e .

# Nebo s pip
pip install -e .
```

### Testování

```bash
# Unit testy
PYTHONPATH=src uv run pytest tests/unit_tests/ -v

# Integration testy
PYTHONPATH=src uv run pytest tests/integration_tests/ -v

# Konkrétní test
PYTHONPATH=src uv run pytest tests/unit_tests/nodes/test_pubmed_agent.py::TestPubMedSearch -v

# Performance benchmarky
PYTHONPATH=src uv run pytest tests/performance/ -v
```

### Kvalita Kódu

```bash
# Type checking (strict mode)
uv run mypy --strict src/agent/nodes/pubmed_agent.py

# Linting
uv run ruff check .

# Formátování
uv run ruff format .

# Kompletní check (všechno najednou)
uv run ruff format . && uv run ruff check . && uv run mypy --strict src/agent/
```

### Vývojový Server

```bash
# Spustit lokální dev server s hot reload
langgraph dev

# Otevře LangGraph Studio na http://localhost:8000
# Auto-reload při změnách kódu
```

### Environment Variables

Vytvořit `.env` z `.env.example`:

```bash
# Volitelný LangSmith tracing
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=czech-medai-dev
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Development
LOG_LEVEL=INFO
```

## Architektura

### Implementované Agents

**Drug Agent (Feature 003)**:
- SÚKL-mcp integration (8 tools)
- Fuzzy search s typo tolerance
- Drug details, PIL/SPC content, reimbursement info
- Document transformation do LangChain format

**PubMed Agent (Feature 005)**:
- BioMCP integration (article_searcher, article_getter)
- Sandwich Pattern: CZ→EN→PubMed→EN→CZ translation
- Citation tracking s inline references [1][2][3]
- Performance <5s latency (SC-001)

### Multi-Agent Pattern (Cílový Stav)

```
User Query (CZ)
    ↓
[route_query] - Klasifikace intentu (drug, research, pricing, guidelines)
    ↓
    ├→ [Drug Agent] → SÚKL-mcp (8 tools) → drug info
    ├→ [Pricing Agent] → VZP LEK-13 (exact search) → ceny & úhrady
    ├→ [PubMed Agent] → BioMCP (24 tools) + CZ→EN→CZ → literatura
    └→ [Guidelines Agent] → ČLS JEP PDFs (pgvector) → guidelines
    ↓
[Citation System] - Konsolidace referencí
    ↓
[Synthesizer Node] - Kombinace outputů
    ↓
Response (CZ) s inline citacemi [1][2][3]
```

### State & Context Pattern

```python
from dataclasses import dataclass, field
from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain_core.documents import Document
from langgraph.runtime import Runtime

# State definition (dataclass)
@dataclass
class State:
    messages: Annotated[list[AnyMessage], add_messages]
    next: str = ""
    retrieved_docs: list[Document] = field(default_factory=list)
    drug_query: DrugQuery | None = None
    research_query: ResearchQuery | None = None

# Context definition (TypedDict for runtime config)
class Context(TypedDict, total=False):
    model_name: str
    temperature: float
    langsmith_project: str
    user_id: str | None
    sukl_mcp_client: Any  # Actual type: SUKLMCPClient (Pydantic compat)
    biomcp_client: Any    # Actual type: BioMCPClient (Pydantic compat)

# Node function signature
async def some_node(
    state: State,
    runtime: Runtime[Context]
) -> dict[str, Any]:
    # Přístup ke konfiguraci
    model = runtime.context.get("model_name", "claude-sonnet-4-5-20250929")

    # Přístup k MCP clients
    sukl_client = runtime.context.get("sukl_mcp_client")

    # Vrátit state updates
    return {
        "messages": [...],
        "next": "next_node_name",
        "retrieved_docs": [...]
    }
```

### Graf Compilation Pattern

```python
from langgraph.graph import StateGraph

graph = (
    StateGraph(State, context_schema=Context)
    .add_node("route_query", route_query)
    .add_node("drug_agent", drug_agent_node)
    .add_node("pubmed_agent", pubmed_agent_node)
    .add_node("translate_cz_to_en", translate_cz_to_en_node)
    .add_node("translate_en_to_cz", translate_en_to_cz_node)
    .add_edge("__start__", "route_query")
    .add_conditional_edges(
        "route_query",
        lambda state: state["next"],
        {
            "drug_agent": "drug_agent",
            "pubmed_agent": "translate_cz_to_en",
            "__end__": "__end__"
        }
    )
    .add_edge("translate_cz_to_en", "pubmed_agent")
    .add_edge("pubmed_agent", "translate_en_to_cz")
    .add_edge("translate_en_to_cz", "__end__")
    .add_edge("drug_agent", "__end__")
    .compile(name="Czech MedAI")
)
```

## Konvence Kódu

### Naming
- **Funkce/Proměnné**: `snake_case` (např. `pubmed_agent_node`)
- **Třídy**: `PascalCase` (např. `State`, `DrugQuery`, `PubMedArticle`)
- **Konstanty**: `UPPER_CASE` (např. `RESEARCH_KEYWORDS`)
- **Node názvy**: lowercase s underscores (např. `"drug_agent"`)

### Docstrings (Google Style)

```python
async def pubmed_agent_node(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    """Search PubMed articles with BioMCP integration.

    Workflow:
        1. Use state.research_query (already populated by translation node)
        2. Call BioMCP article_searcher or article_getter based on query_type
        3. Transform articles to Documents with English abstracts
        4. Return documents (translation to Czech happens in separate node)

    Args:
        state: Current agent state with research_query.
        runtime: Runtime context with biomcp_client.

    Returns:
        Updated state dict with:
            - retrieved_docs: List[Document] with PubMed articles
            - messages: Assistant message with search summary
            - next: "__end__"
    """
```

### Type Hints
- Vždy používat type hints (mypy --strict enforced)
- Pro state fields s reducers použít `Annotated[type, reducer]`
- Vyhýbat se `Any` bez zdůvodnění (dokumentovat exception)
- Use `r"""` docstring prefix pokud obsahuje backslashes

## Testing Architektura

### Fixtures (conftest.py)

```python
import pytest
from agent.graph import State, Context
from agent.models.drug_models import DrugQuery
from agent.models.research_models import ResearchQuery, PubMedArticle

@pytest.fixture(scope="session")
def anyio_backend():
    """Configure asyncio backend for pytest-asyncio."""
    return "asyncio"

@pytest.fixture
def sample_state():
    """Valid State instance pro testování."""
    return State(
        messages=[{"role": "user", "content": "test"}],
        next="placeholder",
        retrieved_docs=[]
    )

@pytest.fixture
def mock_runtime():
    """Mock Runtime s test contextem."""
    class MockRuntime:
        def __init__(self):
            self.context = {
                "model_name": "claude-sonnet-4-5-20250929",
                "temperature": 0.0,
                "sukl_mcp_client": None,
                "biomcp_client": None
            }
    return MockRuntime()

@pytest.fixture
def sample_pubmed_articles():
    """Sample PubMed articles pro testování (5 articles)."""
    return [
        PubMedArticle(
            pmid="12345678",
            title="Efficacy of Metformin in Type 2 Diabetes",
            abstract="Background: Metformin is first-line...",
            authors=["Smith, John", "Doe, Jane"],
            publication_date="2024-06-15",
            journal="NEJM",
            doi="10.1056/NEJMoa2401234"
        ),
        # ... další articles
    ]
```

### Test Structure

```python
@pytest.mark.asyncio
async def test_pubmed_search_returns_documents(
    sample_state, mock_runtime, sample_pubmed_articles
):
    """Test PubMed search vrací dokumenty s correct structure."""
    # Arrange
    from agent.nodes.pubmed_agent import pubmed_agent_node

    state = sample_state
    state["research_query"] = ResearchQuery(
        query_text="diabetes studies",
        query_type="search"
    )

    # Mock BioMCP client
    mock_client = MagicMock()
    mock_client.call_tool = AsyncMock(
        return_value=MCPResponse(
            success=True,
            data={"articles": [...]},
            metadata={}
        )
    )
    mock_runtime.context["biomcp_client"] = mock_client

    # Act
    result = await pubmed_agent_node(state, mock_runtime)

    # Assert
    assert "retrieved_docs" in result
    assert len(result["retrieved_docs"]) > 0
    assert "messages" in result
```

## SpecKit Workflow

Pro vývoj features použijte SpecKit příkazy:

1. **Constitution** (`/speckit.constitution`) - Správa pravidel projektu
2. **Specify** (`/speckit.specify`) - Definovat user stories s kritérii
3. **Plan** (`/speckit.plan`) - Navrhnout graph nody, edges, state změny
4. **Tasks** (`/speckit.tasks`) - Rozdělit na atomické úkoly
5. **Implement** (`/speckit.implement`) - Implementovat s test-first přístupem

## MCP Integration

### SÚKL-mcp (Feature 003)

**Repository**: https://github.com/petrsovadina/SUKL-mcp

**8 Available Tools**:
1. `search_medicine` - Fuzzy search léků
2. `get_medicine_details` - Kompletní info o léku
3. `get_pil_content` - Příbalová informace
4. `get_spc_content` - Souhrn údajů o přípravku
5. `check_availability` - Dostupnost + alternativy
6. `get_reimbursement` - Kategorie úhrad
7. `find_pharmacies` - Vyhledávání lékáren
8. `get_atc_info` - ATC klasifikace

**Usage in Node**:
```python
async def drug_agent_node(state: State, runtime: Runtime[Context]):
    sukl_client = runtime.context.get("sukl_mcp_client")

    result = await sukl_client.call_tool(
        "search_medicine",
        query=drug_name,
        fuzzy=True,
        limit=5
    )

    return {"retrieved_docs": result.documents}
```

### BioMCP (Feature 005)

**Repository**: https://github.com/genomoncology/biomcp

**Key Tools**:
- `article_searcher` - Search PubMed articles
- `article_getter` - Get article by PMID
- `article_recommender` - Get similar articles
- `article_pmc_getter` - Get full text from PMC

**Sandwich Pattern** (CZ→EN→CZ):
```python
# 1. Czech query → Translate to English
state = await translate_cz_to_en_node(state, runtime)

# 2. BioMCP search (English)
state = await pubmed_agent_node(state, runtime)

# 3. Results → Translate to Czech
state = await translate_en_to_cz_node(state, runtime)
```

## Troubleshooting

### Import Issues
- Vždy importovat z `agent.graph`, ne `src.agent.graph`
- Package discovery v pyproject.toml: `[tool.setuptools.packages.find]`
- PYTHONPATH=src při spouštění testů

### Type Checking
- `mypy --strict` enforced - žádné implicitní Any
- Use `Any` s doc comment pro MCP clients (Pydantic compat)
- `total=False` na TypedDict pro optional fields

### Testing
- Použít `@pytest.mark.asyncio` pro async testy
- Mock MCP clients s `AsyncMock` pro async call_tool
- PYTHONPATH=src required: `PYTHONPATH=src uv run pytest`

### Translation Tests
- 5 translation testů vyžaduje Anthropic API kredity
- Mock LLM responses v unit testech
- Use `ChatAnthropic(model_name=..., temperature=0, timeout=None, stop=None)`

## Důležité Soubory

1. **`.specify/memory/constitution.md`** - Constitution v1.0.3 (single source of truth)
2. **`src/agent/graph.py`** - Core graph definice (route_query, State, Context)
3. **`src/agent/nodes/`** - Node implementace (drug_agent, pubmed_agent, translation)
4. **`src/agent/mcp/`** - MCP client wrappers (adapters, domain, config)
5. **`src/agent/models/`** - Pydantic models (drug_models, research_models)
6. **`pyproject.toml`** - Závislosti & ruff/mypy konfigurace
7. **`tests/conftest.py`** - Pytest fixtures (anyio_backend, mocks, samples)
8. **`specs/ROADMAP.md`** - Master roadmap všech features

## Reference

### Framework & Tools
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangSmith**: https://docs.smith.langchain.com/

### MCP Servery
- **SÚKL-mcp Repository**: https://github.com/petrsovadina/SUKL-mcp
- **BioMCP Repository**: https://github.com/genomoncology/biomcp

### Project Documentation
- **Constitution**: `.specify/memory/constitution.md` (v1.0.3)
- **Specs**: `specs/` directory (001-005 dostupné)
- **Roadmap**: `specs/ROADMAP.md`

---

**Poslední aktualizace**: 2026-01-23
**Aktuální větev**: 005-biomcp-pubmed-agent
**Main větev**: main
**Status projektu**: Fáze 1 (Core Agents) - 3/4 agentů dokončeno (Drug, PubMed), Pricing čeká
**Constitution**: v1.0.3 (Phase 7 quality standards codified)
**Test Coverage**: 169/175 passing (96%)
