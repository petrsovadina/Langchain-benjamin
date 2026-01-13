# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Czech MedAI (Benjamin)** je multi-agentní AI asistent pro české lékaře, postavený na LangGraph frameworku. Systém poskytuje klinickou rozhodovací podporu založenou na důkazech, integrující specializované AI agenty pro dotazování českých medicínských zdrojů (SÚKL, VZP, ČLS JEP) a mezinárodního výzkumu (PubMed) s kompletním sledováním citací.

**Současný stav**: Fáze 0 (Foundation) - Větev `001-langgraph-foundation`
- Specifikace dokončeny
- Základní šablona grafu připravena
- Připraveno k implementaci AgentState/Context

## Technologie

- **Framework**: LangGraph ≥1.0.0 (multi-agent orchestrace)
- **Jazyk**: Python ≥3.10 (async-first architektura)
- **MCP Servery**:
  - **SÚKL-mcp** - Czech pharmaceutical database (68k+ léků)
  - **BioMCP** - Biomedical databases (PubMed, ClinicalTrials, atd.)
- **Testing**: pytest s async podporou
- **Kvalita kódu**: ruff (linting/formátování), mypy (strict type checking)
- **Observability**: LangSmith tracing

## Struktura Projektu

```
langgraph-app/              # Hlavní aplikace (Python balíček)
├── src/agent/
│   ├── __init__.py        # Export balíčku
│   └── graph.py           # Definice grafu (K IMPLEMENTACI)
├── tests/
│   ├── conftest.py        # pytest fixtures
│   ├── unit_tests/        # Unit testy pro nody
│   └── integration_tests/ # Integrační testy pro graf
├── pyproject.toml         # Závislosti & konfigurace nástrojů
├── Makefile               # Vývojové příkazy
└── langgraph.json         # LangGraph server konfigurace

specs/                     # Specifikace features
├── 001-langgraph-foundation/
│   ├── spec.md           # User stories, požadavky
│   ├── plan.md           # Implementační plán
│   └── tasks.md          # Rozpad úkolů
└── ROADMAP.md            # Master roadmap (12 features, 4 fáze)

.specify/                  # SpecKit framework
├── memory/
│   └── constitution.md   # Constitution projektu (5 principů)
└── templates/            # Šablony pro spec/plan/tasks
```

## Constitution Projektu

Projekt je řízen 5 základními principy v `.specify/memory/constitution.md` (verze 1.0.1):

### I. Graph-Centric Architecture
- **VŠECHNY** features MUSÍ být implementovány jako LangGraph nody a hrany
- Node funkce MUSÍ být async: `async def node_name(state: State, runtime: Runtime[Context]) -> Dict[str, Any]`
- State transitions MUSÍ být explicitní přes `.add_edge()` nebo conditional edges
- Graf MUSÍ být vizualizovatelný v LangGraph Studio

### II. Type Safety & Schema Validation
- **VŠE** state a context MUSÍ používat typed dataclasses/TypedDict
- `State` definuje všechna pole grafu s type hints
- `Context` TypedDict definuje runtime konfigurační parametry
- Použití mypy --strict pro type checking

### III. Test-First Development (NEPORUŠITELNÉ)
- **Testy MUSÍ být napsány PŘED implementací**
- Unit testy v `tests/unit_tests/`
- Integrační testy v `tests/integration_tests/`
- Workflow: Napsat test → Fail → Implementovat → Pass
- Cílové pokrytí: ≥80%

### IV. Observability & Debugging
- **VŠECHNY** graph executions MUSÍ být sledovatelné
- LangSmith tracing přes `.env` (`LANGSMITH_API_KEY`)
- Logování state transitions
- Použití LangGraph Studio pro vizuální debugging

### V. Modular & Extensible Design
- Každý node MUSÍ mít jednu jasnou zodpovědnost
- Preference vícero malých nodů než jeden velký
- Konfigurace v `Context`, ne hardcoded

## Běžné Příkazy

### Setup

```bash
cd langgraph-app

# Instalace závislostí
pip install -e .
pip install langgraph-cli[inmem]

# Nebo s uv (rychlejší)
uv venv
uv pip install -e .
uv pip install langgraph-cli[inmem]
```

### Vývojový Server

```bash
# Spustit lokální dev server s hot reload
langgraph dev

# Otevře LangGraph Studio na http://localhost:8000
# Auto-reload při změnách kódu
```

### Testování

```bash
make test                    # Spustit unit testy
make integration_tests       # Spustit integrační testy
make test_watch             # Watch mode - rerun při změnách
make test TEST_FILE=path/   # Spustit konkrétní test

# Kontrola pokrytí
make test_profile           # Generovat profile-svg report
```

### Kvalita Kódu

```bash
make lint                   # Kontrola s ruff + mypy (strict)
make format                 # Formátovat kód s ruff
make lint_diff             # Lintovat pouze změněné soubory
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

### Multi-Agent Pattern

```
User Query
    ↓
[Supervisor Node] - Klasifikace intentu (8 typů)
    ↓
    ├→ [Drug Agent] → SÚKL data (pgvector search)
    ├→ [Pricing Agent] → VZP LEK-13 (exact search)
    ├→ [PubMed Agent] → BioMCP (article_searcher service)
    └→ [Guidelines Agent] → ČLS JEP PDFs (vector search)
    ↓
[Citation System] - Konsolidace referencí
    ↓
[Synthesizer Node] - Kombinace outputů
    ↓
Response s inline citacemi [1][2][3]
```

### State & Context Pattern

```python
from typing import Any, Dict, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain_core.documents import Document
from langgraph.runtime import Runtime

# State definition (TypedDict s annotations)
class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    next: str
    retrieved_docs: list[Document]

# Context definition (runtime config)
class Context(TypedDict, total=False):
    model_name: str
    temperature: float
    langsmith_project: str

# Node function signature
async def some_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    # Přístup ke konfiguraci
    model = runtime.context.get("model_name", "default")

    # Vrátit state updates
    return {
        "messages": [...],
        "next": "next_node_name"
    }
```

### Graf Compilation Pattern

```python
from langgraph.graph import StateGraph

graph = (
    StateGraph(State, context_schema=Context)
    .add_node("node_name", async_function)
    .add_edge("__start__", "node_name")
    .add_conditional_edges("node_name", routing_function)
    .add_edge("node_name", "__end__")
    .compile(name="Czech MedAI")
)
```

## Konvence Kódu

### Naming
- **Funkce/Proměnné**: `snake_case` (např. `placeholder_node`)
- **Třídy**: `PascalCase` (např. `State`, `Context`)
- **Konstanty**: `UPPER_CASE` (např. `MAX_RETRIES`)
- **Node názvy**: lowercase s underscores (např. `"placeholder_node"`)

### Docstrings (Google Style)

```python
def placeholder_node(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Echo user messages with configuration info.

    Processes input state and returns AI response using configured model.

    Args:
        state: Current agent state with message history.
        runtime: Runtime context with model configuration.

    Returns:
        Updated state dict with:
            - messages: list with new assistant message
            - next: routing indicator for next node

    Raises:
        ValueError: If state.messages is empty.
    """
```

### Type Hints
- Vždy používat type hints (mypy --strict enforced)
- Pro state fields s reducers použít `Annotated[type, reducer]`
- Vyhýbat se `Any` bez zdůvodnění

## Testing Architektura

### Fixtures (conftest.py)

```python
import pytest
from agent.graph import State, Context, graph

@pytest.fixture(scope="session")
def anyio_backend():
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
                "model_name": "test-model",
                "temperature": 0.0
            }
    return MockRuntime()
```

### CI/CD
- **Unit Tests**: Běží při každém push (Python 3.11, 3.12)
- **Integration Tests**: Denně v 14:37 UTC (vyžaduje API klíče)

## SpecKit Workflow

Pro vývoj features použijte SpecKit příkazy (dostupné v `.github/agents/`):

1. **Constitution** (`speckit.constitution`) - Správa pravidel projektu
2. **Specify** (`speckit.specify`) - Definovat user stories s kritérii
3. **Plan** (`speckit.plan`) - Navrhnout graph nody, edges, state změny
4. **Tasks** (`speckit.tasks`) - Rozdělit na atomické úkoly
5. **Implement** (`speckit.implement`) - Implementovat s test-first přístupem

## Implementační Roadmap

### Fáze 0: Foundation (Aktuální - Týdny 1-2)
- **001-langgraph-foundation** (5 dní, KRITICKÉ)
  - Definovat `AgentState` a `Context`
  - Vytvořit pytest fixtures
  - Setup LangSmith tracing
  - ✓ Spec hotová, implementace zahájena

- **002-mcp-infrastructure** (4 dny, KRITICKÉ, paralelně)
  - Setup MCP protocol
  - Konfigurace Docker pro BioMCP
  - Supabase s pgvector

### Fáze 1: Core Agents (Týdny 3-6)
- **003-sukl-drug-agent** (8 dní) - Informace o lécích
- **004-vzp-pricing-agent** (6 dní) - Ceny & úhrady
- **005-biomcp-pubmed-agent** (7 dní) - Výzkumná literatura
- **006-guidelines-agent** (8 dní) - Klinické guidelines

### Fáze 2: Integration (Týdny 7-9)
- **007-supervisor-orchestration** (9 dní) - Intent routing
- **008-citation-system** (6 dní) - Evidence tracking
- **009-synthesizer-node** (5 dní) - Response synthesis

### Fáze 3: UX & Deployment (Týdny 10-12)
- **010-czech-localization** (4 dny) - České lokalizace
- **011-fastapi-backend** (6 dní) - REST API
- **012-nextjs-frontend** (10 dní) - Chat interface

## Důležité Soubory

1. **`.specify/memory/constitution.md`** - Constitution projektu (single source of truth)
2. **`langgraph-app/src/agent/graph.py`** - Core graph definice
3. **`langgraph-app/pyproject.toml`** - Závislosti & konfigurace
4. **`langgraph-app/langgraph.json`** - LangGraph server config
5. **`specs/ROADMAP.md`** - Master roadmap všech features

## Troubleshooting

### Import Issues
- Vždy importovat z `agent.graph`, ne relativní cesty
- Použít `from typing_extensions import TypedDict` pro Python 3.10 kompatibilitu

### Type Checking
- `mypy --strict` je enforced - žádné implicitní Any
- Použít `total=False` na TypedDict pro optional fields

### Async/Await
- Všechny node funkce MUSÍ být async
- Použít `@pytest.mark.asyncio` pro async testy

### LangSmith
- Pokud chybí LANGSMITH_API_KEY, tracing gracefully degraduje (nespadne)
- Nastavit LANGSMITH_PROJECT v .env pro organizaci traces

## MCP Integration

Czech MedAI integruje **2 klíčové MCP servery** pro přístup k medicínským datům:

### 1. SÚKL-mcp (Czech Pharmaceutical Database)

**Repository**: https://github.com/petrsovadina/SUKL-mcp

**Purpose**: Oficiální databáze léků SÚKL s 68,248 registrovanými léky

**Features**:
- Fuzzy search s tolerance pro překlepy (rapidfuzz, threshold 80)
- Hybrid architektura (REST API + CSV fallback)
- Automatické parsování PDF/Word dokumentů
- Multi-kriteriální ranking pro alternativy
- Informace o cenách a úhradách (VZP)

**Available Tools (8)**:
1. `search_medicine` - Vyhledávání léků s fuzzy matching
2. `get_medicine_details` - Kompletní info o léku včetně složení
3. `get_pil_content` - Příbalová informace (PIL)
4. `get_spc_content` - Souhrn údajů o přípravku (SPC)
5. `check_availability` - Dostupnost + automatické alternativy
6. `get_reimbursement` - Kategorie úhrad (A/B/D) a předepisovatelnost
7. `find_pharmacies` - Vyhledávání lékáren podle lokace
8. `get_atc_info` - ATC klasifikace

**Installation**:
```bash
# Production server
claude mcp add --scope local --transport http SUKL-mcp https://SUKL-mcp.fastmcp.app/mcp

# Local development
git clone https://github.com/DigiMedic/SUKL-mcp.git
cd SUKL-mcp
pip install -e ".[dev]"
python -m sukl_mcp
```

**Integration Point**: Feature **003-sukl-drug-agent**

**Czech-Specific**:
- Data z SÚKL Open Data portálu (měsíční update)
- Windows-1250 encoding support
- České healthcare terminologie (ATC, kategorie úhrad)

---

### 2. BioMCP (Biomedical Model Context Protocol)

**Repository**: https://github.com/genomoncology/biomcp

**Purpose**: Přístup k biomedical databases (PubMed, ClinicalTrials, atd.)

**Features**:
- 24 specialized tools pro biomedicínská data
- Sequential reasoning s "think" tool
- Natural language queries (bez SQL syntaxe)
- Enterprise-grade MCP server

**Data Sources**:
- **Literature**: PubMed/PubTator3, bioRxiv/medRxiv, Europe PMC
- **Clinical**: ClinicalTrials.gov, NCI Clinical Trials API
- **Genomic**: MyVariant.info, MyGene.info, MyDisease.info, MyChem.info
- **Regulatory**: OpenFDA (FAERS, SPL, MAUDE)

**Available Tools (24)**:
- **Core (3)**: `think`, `search`, `fetch`
- **Articles (4)**: `article_searcher`, `article_getter`, `article_recommender`, `article_pmc_getter`
- **Trials (6)**: `trial_searcher`, `trial_getter`, `trial_nci_searcher`, atd.
- **Variants (3)**: `variant_searcher`, `variant_getter`, `variant_annotator`
- **Genes/Diseases (8)**: `gene_getter`, `disease_getter`, atd.

**Installation**:
```bash
# For Claude Desktop
# 1. Install uv package manager
# 2. Configure Claude Desktop:
{
  "mcpServers": {
    "biomcp": {
      "command": "uv",
      "args": ["run", "--with", "biomcp-python", "biomcp", "run"]
    }
  }
}

# Python package
uv pip install biomcp-python
# nebo
pip install biomcp-python
```

**Integration Point**: Feature **005-biomcp-pubmed-agent**

**Sandwich Pattern** (CZ→EN→CZ):
1. Czech query → Translate to English
2. BioMCP search (English)
3. Results → Translate to Czech

---

### MCP Architecture v Czech MedAI

```
User Query (CZ)
    ↓
[Supervisor Node]
    ↓
    ├─→ [Drug Agent] → SÚKL-mcp (8 tools)
    ├─→ [Pricing Agent] → VZP LEK-13 (direct)
    ├─→ [PubMed Agent] → BioMCP (24 tools) + CZ→EN→CZ translation
    └─→ [Guidelines Agent] → ČLS JEP PDFs (pgvector)
    ↓
[Citation System]
    ↓
Response (CZ) s citacemi [1][2][3]
```

### MCP Development Workflow

**Feature 002-mcp-infrastructure** setup:
1. Install both MCP servers locally
2. Configure Claude Desktop integration
3. Create MCP client wrappers v `src/agent/mcp/`
4. Setup async communication patterns
5. Error handling & fallback strategies

**Testing MCP integration**:
```bash
# Test SÚKL-mcp
python -c "import httpx; print(httpx.get('https://SUKL-mcp.fastmcp.app/health').json())"

# Test BioMCP locally
biomcp article search --gene BRAF --disease Melanoma
```

**MCP Tools Usage in Nodes**:
```python
async def drug_agent_node(state: State, runtime: Runtime[Context]):
    """Query SÚKL-mcp for drug information."""
    # Use MCP client wrapper
    sukl_client = runtime.context.get("sukl_mcp_client")

    # Call SÚKL tool
    result = await sukl_client.call_tool(
        "search_medicine",
        query=drug_name,
        fuzzy=True
    )

    return {"retrieved_docs": result.documents}
```

### MCP Configuration (.env)

```bash
# SÚKL-mcp
SUKL_MCP_URL=https://SUKL-mcp.fastmcp.app/mcp
SUKL_MCP_TRANSPORT=http

# BioMCP
BIOMCP_TRANSPORT=stdio
BIOMCP_COMMAND=biomcp run

# Fallback mode
ENABLE_MCP_FALLBACK=true
```

## Reference

### Framework & Tools
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **LangSmith**: https://docs.smith.langchain.com/

### MCP Servery
- **SÚKL-mcp Repository**: https://github.com/petrsovadina/SUKL-mcp
- **BioMCP Repository**: https://github.com/genomoncology/biomcp
- **MCP Integration Guide**: `MCP_INTEGRATION.md`

### Architectural Inspiration
- **BioAgents Repository**: https://github.com/bio-xyz/BioAgents
- **BioAgents Patterns**: `BIOAGENTS_INSPIRATION.md`

### Project Documentation
- **Constitution**: `.specify/memory/constitution.md`
- **Specs**: `specs/` directory
- **Roadmap**: `specs/ROADMAP.md`

---

**Poslední aktualizace**: 2026-01-13
**Aktuální větev**: 001-langgraph-foundation
**Main větev**: main
**Status projektu**: Foundation fáze - specifikace hotové, implementace probíhá
