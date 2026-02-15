# Czech MedAI - Development Guide

**Version**: 0.1.0 | **Last Updated**: 2026-02-15

## Prerequisites

- Python >= 3.10 (dev uses 3.12)
- Node.js >= 18 (for frontend)
- Docker + Docker Compose (for infrastructure services)
- `uv` package manager (Python)

## Quick Start

### Backend

```bash
cd langgraph-app

# Install dependencies
uv pip install -e .

# Copy environment template
cp .env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY required)

# Start infrastructure (PostgreSQL + Redis)
docker compose up redis postgres -d

# Run dev server (LangGraph Studio)
./dev.sh
# Or manually:
PYTHONPATH=src langgraph dev
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
# → http://localhost:3000
```

### FastAPI Bridge (production mode)

```bash
cd langgraph-app
PYTHONPATH=src uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Agent Node Development

All agent nodes follow the same contract defined by LangGraph and the project
constitution (Principle I).

### Node Signature

```python
async def my_agent_node(
    state: State,
    runtime: Runtime[Context],
) -> dict[str, Any]:
    """Node docstring (Google-style, required).

    Args:
        state: Current graph state with messages and retrieved_docs.
        runtime: Runtime with Context (model_name, MCP clients, mode).

    Returns:
        Dict with updated State fields (messages, retrieved_docs, next).
    """
```

### Node Location

All agent nodes reside in `langgraph-app/src/agent/nodes/` as separate modules.
Each module exports a single `*_node` function and is registered in
`nodes/__init__.py`.

### Accessing MCP Clients

```python
from agent.graph import get_mcp_clients

async def my_node(state: State, runtime: Runtime[Context]) -> dict[str, Any]:
    sukl_client, biomcp_client = get_mcp_clients(runtime)

    if sukl_client is None:
        # Graceful degradation
        return {"messages": [...], "next": "__end__"}

    result = await sukl_client.call_tool("search_medicine", {"query": "..."})
```

`get_mcp_clients()` checks `runtime.context` first (for test overrides), then
falls back to module-level clients initialized from environment variables.

### Adding a New Node

1. Create `langgraph-app/src/agent/nodes/my_agent.py`
2. Export from `nodes/__init__.py`
3. Register in `graph.py`:
   ```python
   .add_node("my_agent", my_agent_node)
   .add_edge("my_agent", "synthesizer")
   ```
4. Add routing in `supervisor.py` (intent classification + keyword fallback)
5. Add SSE event filtering in `routes.py`
6. Write tests in `tests/unit_tests/nodes/test_my_agent.py`

### Existing Nodes

| Node | Module | Responsibility |
|------|--------|---------------|
| `supervisor` | `nodes/supervisor.py` | LLM intent classification → Send API dispatch |
| `drug_agent` | `nodes/drug_agent.py` | SUKL pharmaceutical DB queries (JSON-RPC) |
| `pubmed_agent` | `nodes/pubmed_agent.py` | PubMed search with internal CZ→EN translation |
| `guidelines_agent` | `nodes/guidelines_agent.py` | Clinical guidelines via pgvector semantic search |
| `general_agent` | `nodes/general_agent.py` | General medical Q&A via Claude LLM |
| `synthesizer` | `nodes/synthesizer.py` | Response merge, citation numbering, terminology |

---

## Routing System

### How Routing Works

The supervisor uses a two-tier routing strategy:

1. **LLM Intent Classification** (primary) — Claude classifies the query into
   one of 8 intent types and maps them to agent names
2. **Keyword Fallback** — if LLM classification fails, `fallback_to_keyword_routing()`
   matches Czech/English keywords

### Routing Priority (Keywords)

```
Drug keywords (highest) → Research keywords → Guidelines keywords → General (default)
```

`fallback_to_keyword_routing()` in `supervisor.py` is the **single source of truth**
for keyword-based routing. `route_query()` in `graph.py` delegates to it.

### Adding Keywords

Edit the keyword sets in `graph.py`:

```python
DRUG_KEYWORDS = {"lék", "léky", "dávkování", ...}
RESEARCH_KEYWORDS = {"studie", "výzkum", "pubmed", ...}
GUIDELINES_KEYWORDS = {"guidelines", "doporučené postupy", ...}
```

After modifying keywords, add regression tests in
`tests/unit_tests/test_routing.py`.

---

## MCP Client Development

### Architecture

MCP clients follow Hexagonal Architecture:

```
IMCPClient (port/interface)
├── SUKLMCPClient (adapter, JSON-RPC 2.0)
└── BioMCPClient (adapter, REST)
```

### IMCPClient Interface

```python
class IMCPClient(ABC):
    async def call_tool(self, tool_name, parameters, retry_config=None) -> MCPResponse
    async def health_check(self, timeout=5.0) -> MCPHealthStatus
    async def list_tools(self) -> list[MCPToolMetadata]
    async def close(self) -> None
```

### Creating a New MCP Adapter

1. Create `agent/mcp/adapters/my_client.py`
2. Implement `IMCPClient` interface
3. Add async context manager support (`__aenter__`/`__aexit__`)
4. Register in `agent/mcp/__init__.py`
5. Add to `MCPConfig` in `agent/mcp/domain/entities.py`

### Key Conventions

- JSON-RPC clients use `_build_rpc_request()` helper
- All HTTP clients must implement async context manager
- Content size limits: 1MB total, 100KB per field
- 30s default timeout for external calls
- Thread-safe ID generation via `itertools.count()`

---

## Testing

### Running Tests

```bash
cd langgraph-app

# All unit tests
PYTHONPATH=src uv run pytest tests/unit_tests/ -v

# Specific test file
PYTHONPATH=src uv run pytest tests/unit_tests/nodes/test_drug_agent.py -v

# Specific test class
PYTHONPATH=src uv run pytest tests/unit_tests/nodes/test_supervisor.py::TestSupervisorNode -v

# Integration tests
PYTHONPATH=src uv run pytest tests/integration_tests/ -v

# With coverage
PYTHONPATH=src uv run pytest tests/unit_tests/ --cov=agent --cov-report=term-missing
```

### Test Conventions

- `asyncio_mode = "auto"` — no `@pytest.mark.asyncio` decorator needed
- Always `patch("agent.graph.get_mcp_clients")` to prevent real MCP connections
- Use `AsyncMock` for MCP client mocks
- Fixtures in `tests/conftest.py`: `mock_runtime`, `sample_state`, `sample_pubmed_articles`
- 5 translation tests require API keys (expected skips in local dev)

### Writing a Node Test

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from agent.nodes.my_agent import my_agent_node


@pytest.fixture
def mock_runtime():
    runtime = MagicMock()
    runtime.context = {
        "model_name": "claude-sonnet-4-5-20250929",
        "temperature": 0.0,
    }
    return runtime


@pytest.fixture
def sample_state():
    return MagicMock(
        messages=[MagicMock(content="test query")],
        retrieved_docs=[],
    )


class TestMyAgent:
    async def test_basic_query(self, sample_state, mock_runtime):
        with patch("agent.graph.get_mcp_clients") as mock_clients:
            mock_clients.return_value = (None, None)
            result = await my_agent_node(sample_state, mock_runtime)
            assert "messages" in result
```

### Test Structure

```
tests/
├── unit_tests/
│   ├── nodes/           # Per-node tests
│   │   ├── test_supervisor.py
│   │   ├── test_drug_agent.py
│   │   └── ...
│   ├── mcp/             # MCP client tests
│   ├── test_routing.py  # Keyword routing regression tests
│   └── test_graph.py    # Graph structure tests
├── integration_tests/   # Full graph execution
├── quality/             # Code quality checks
├── performance/         # Latency benchmarks
└── conftest.py          # Shared fixtures
```

---

## Code Quality

### Linting & Formatting

```bash
cd langgraph-app

# Format
uv run ruff format .

# Lint
uv run ruff check .

# Type check (strict)
uv run mypy --strict src/agent/

# All at once
uv run ruff format . && uv run ruff check . && uv run mypy --strict src/agent/
```

### ruff Configuration

Enabled rule sets: E (pycodestyle), F (pyflakes), I (isort), D (pydocstyle),
D401, T201 (no print), UP (pyupgrade).

Per-file ignores:
- `tests/*`: D (docstrings), UP, T201
- `src/*`: T201 (print allowed for debugging)

### Type Safety

- `mypy --strict` — zero errors required
- Exception: `Any` with doc comment for MCP clients in Context (Pydantic compat)
- All function signatures need complete type hints

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key for supervisor + agent LLM calls |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | Guidelines embeddings (pgvector) |
| `SUKL_MCP_URL` | `http://localhost:3001` | SUKL MCP server URL |
| `BIOMCP_COMMAND` | — | BioMCP REST client command |
| `DATABASE_URL` | — | PostgreSQL + pgvector connection |
| `REDIS_URL` | `redis://localhost:6379` | Response cache |
| `LANGSMITH_API_KEY` | — | LangSmith tracing |
| `LANGSMITH_PROJECT` | `czech-medai-dev` | LangSmith project name |
| `TRANSLATION_MODEL` | `claude-4.5-haiku` | Model for CZ↔EN translation |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |

---

## Docker

### Development

```bash
cd langgraph-app

# Start all services
docker compose up

# Start only infrastructure
docker compose up redis postgres -d
```

### Services

| Service | Port | Purpose |
|---------|------|---------|
| `api` | 8000 | FastAPI + LangGraph (4 uvicorn workers) |
| `redis` | 6379 | Response cache (256MB, allkeys-lru) |
| `postgres` | 5432 | pgvector for clinical guidelines |

### Health Check

```bash
curl http://localhost:8000/health | python -m json.tool
```

---

## Feature Development Workflow (SpecKit)

```bash
cd langgraph-app
make speckit_new FEATURE="Description"

# Then in Claude Code:
# /speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

Feature specs live in `specs/NNN-feature-name/` with `spec.md`, `plan.md`,
`tasks.md`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'agent'` | Use `PYTHONPATH=src` prefix or `./dev.sh` |
| `uv run pytest` hangs on import | Use `.venv/bin/pytest` with `PYTHONPATH=src` |
| Translation tests skip | Expected without `ANTHROPIC_API_KEY` in `.env` |
| Tests leak to real MCP servers | Always `patch("agent.graph.get_mcp_clients")` |
| Frontend can't connect to backend | Ensure FastAPI on :8000, `NEXT_PUBLIC_API_URL` set |
| Port 2024 already in use | Kill zombie process: `lsof -ti:2024 \| xargs kill` |
