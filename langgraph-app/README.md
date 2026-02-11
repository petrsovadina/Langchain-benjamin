# Czech MedAI - Backend (LangGraph + FastAPI)

Multi-agentní LangGraph graf s FastAPI bridge vrstvou pro Czech MedAI.

## Quick Start

```bash
# Setup
uv venv && source .venv/bin/activate
uv pip install -e .
uv pip install 'langgraph-cli[inmem]'
cp .env.example .env

# Dev server (LangGraph Studio)
./dev.sh

# FastAPI server
PYTHONPATH=src uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Graph Architecture

```
__start__ → supervisor (LLM intent + Send API)
              ├→ drug_agent → synthesizer
              ├→ translate_cz_to_en → pubmed_agent → translate_en_to_cz → synthesizer
              ├→ guidelines_agent → synthesizer
              └→ placeholder → synthesizer
           synthesizer → __end__
```

Defined in `src/agent/graph.py`, configured via `langgraph.json`.

### Nodes

| Node | File | Role |
|---|---|---|
| `supervisor` | `nodes/supervisor.py` | LLM intent classification, Send API dispatch |
| `drug_agent` | `nodes/drug_agent.py` | SÚKL drug queries via MCP |
| `pubmed_agent` | `nodes/pubmed_agent.py` | PubMed search via BioMCP |
| `translate_*` | `nodes/translation.py` | CZ↔EN translation (Sandwich Pattern) |
| `guidelines_agent` | `nodes/guidelines_agent.py` | ČLS JEP guideline search (pgvector) |
| `synthesizer` | `nodes/synthesizer.py` | Multi-agent response combination |

### FastAPI Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/consult` | POST | SSE streaming consultation |
| `/health` | GET | Health check (MCP clients, DB) |

## Development

```bash
make test                    # Unit testy
make integration_tests       # Integrační testy
make test TEST_FILE=path     # Konkrétní test
make lint                    # ruff + mypy --strict
make format                  # Auto-format
make spell_check             # Spell check
make speckit_help            # SpecKit workflow help
```

## Guidelines Storage (pgvector)

```bash
# Migration
psql -d your_database -f migrations/003_guidelines_schema.sql

# Environment
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
```

```python
from agent.utils.guidelines_storage import store_guideline, search_guidelines
from agent.models.guideline_models import GuidelineSection, GuidelineSource

section = GuidelineSection(
    guideline_id="CLS-JEP-2024-001",
    title="Hypertenze",
    section_name="Farmakologická léčba",
    content="ACE inhibitory jsou...",
    publication_date="2024-01-15",
    source=GuidelineSource.CLS_JEP,
    url="https://www.cls.cz/guidelines/hypertenze-2024.pdf",
    metadata={"embedding": [0.1] * 1536}
)
await store_guideline(section)

results = await search_guidelines(query=[0.1] * 1536, limit=5, source_filter="cls_jep")
```

## Docker (Production)

```bash
docker compose up            # API + Redis + PostgreSQL
```
