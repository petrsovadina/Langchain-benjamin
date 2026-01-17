# Quickstart: SÚKL Drug Agent

**Feature**: 003-sukl-drug-agent
**Date**: 2026-01-17

## Přehled

SÚKL Drug Agent je LangGraph node pro vyhledávání informací o lécích v české databázi SÚKL (68,000+ léků).

## Prerekvizity

1. **Feature 002 dokončena** - MCP Infrastructure
2. **Python ≥3.10**
3. **SÚKL-mcp server** běžící (nebo mock pro testy)

## Rychlý start

### 1. Instalace

```bash
cd langgraph-app
pip install -e .
```

### 2. Konfigurace

Nastavte `.env`:

```bash
# SÚKL-mcp server
SUKL_MCP_URL=http://localhost:3000
SUKL_MCP_TIMEOUT=30.0

# LangSmith (optional)
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=czech-medai-dev
```

### 3. Použití

```python
from agent.graph import graph, State, Context
from agent.mcp import SUKLMCPClient, MCPConfig

# Inicializace klienta
config = MCPConfig.from_env()
sukl_client = SUKLMCPClient(base_url=config.sukl_url)

# Vytvoření kontextu
context: Context = {
    "model_name": "claude-sonnet-4",
    "sukl_mcp_client": sukl_client,
    "mode": "quick"
}

# Spuštění grafu
result = await graph.ainvoke(
    State(messages=[{"role": "user", "content": "Najdi informace o léku Ibalgin"}]),
    {"configurable": {"context": context}}
)

# Výsledky
for doc in result["retrieved_docs"]:
    print(f"📋 {doc.page_content}")
    print(f"   Zdroj: {doc.metadata['source']}")
```

### 4. Spuštění serveru

```bash
langgraph dev
# Otevřít http://localhost:8000 (LangGraph Studio)
```

## Typy dotazů

| Příklad dotazu | Typ | Výsledek |
|----------------|-----|----------|
| "Najdi Ibalgin" | search | Seznam léků odpovídajících názvu |
| "Složení Paralenu" | details | Detailní info včetně účinné látky |
| "Kolik stojí Ibuprofen?" | reimbursement | Cena a kategorie úhrady |
| "Je Ibalgin dostupný?" | availability | Dostupnost + alternativy |
| "Léky s ATC M01AE01" | atc | Seznam léků s daným ATC kódem |
| "Léky s ibuprofenen" | ingredient | Seznam léků s účinnou látkou |

## Testování

```bash
# Unit testy
pytest tests/unit_tests/nodes/test_drug_agent.py -v

# Integration testy
pytest tests/integration_tests/test_drug_agent_flow.py -v

# Coverage
pytest tests/unit_tests/nodes/ --cov=agent.nodes --cov-report=term-missing
```

## Troubleshooting

### SÚKL server není dostupný

```
MCPConnectionError: Cannot connect to SÚKL server
```

**Řešení**: Ověřte, že SÚKL-mcp server běží na konfigurované URL.

### Timeout

```
MCPTimeoutError: SÚKL request timeout
```

**Řešení**: Zvyšte `SUKL_MCP_TIMEOUT` nebo zúžte vyhledávání.

### Žádné výsledky

```
NoResultsError: Žádný lék nenalezen
```

**Řešení**: Ověřte správnost názvu léku. Zkuste fuzzy search.

## Další kroky

1. Přidat node do grafu v `src/agent/graph.py`
2. Napsat unit testy (TDD workflow)
3. Ověřit v LangGraph Studio
4. Integrovat s budoucím Supervisor (Feature 007)
