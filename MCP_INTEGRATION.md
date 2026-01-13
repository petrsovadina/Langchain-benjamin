# MCP Integration Guide - Czech MedAI

Complete guide pro integraci Model Context Protocol (MCP) serverů do Czech MedAI multi-agent systému.

## 📋 Obsah

1. [Přehled MCP Serverů](#přehled-mcp-serverů)
2. [SÚKL-mcp Integration](#súkl-mcp-integration)
3. [BioMCP Integration](#biomcp-integration)
4. [Development Setup](#development-setup)
5. [Testing MCP Connections](#testing-mcp-connections)
6. [Architecture Patterns](#architecture-patterns)
7. [Troubleshooting](#troubleshooting)

---

## Přehled MCP Serverů

Czech MedAI používá **2 klíčové MCP servery**:

| Server | Purpose | Features | Tools | Integration Point |
|--------|---------|----------|-------|-------------------|
| **SÚKL-mcp** | Czech pharmaceutical DB | 68k+ léků, fuzzy search, úhrady | 8 | Feature 003 |
| **BioMCP** | Biomedical databases | PubMed, ClinicalTrials, variants | 24 | Feature 005 |

### Why MCP?

MCP (Model Context Protocol) poskytuje:
- ✅ **Standardizované rozhraní** pro AI agents
- ✅ **Type-safe communication** s external datasources
- ✅ **Async by default** - kompatibilní s LangGraph
- ✅ **Error handling & retry logic** built-in
- ✅ **Observable & traceable** přes LangSmith

---

## SÚKL-mcp Integration

### 🎯 Use Case

Agent potřebuje informace o českých lécích:
- Vyhledání léku podle názvu (s tolerance pro překlepy)
- Detaily o složení, dávkování, kontraindikacích
- Informace o dostupnosti a alternativách
- Ceny a úhrady (kategorie A/B/D)
- Příbalová informace (PIL) a Souhrn údajů (SPC)

### 📦 Repository

**GitHub**: https://github.com/petrsovadina/SUKL-mcp
**Production Server**: https://SUKL-mcp.fastmcp.app/mcp

### 🛠️ Installation

#### Option A: Production Server (Recommended)

```bash
# Add to Claude Desktop
claude mcp add --scope local --transport http SUKL-mcp https://SUKL-mcp.fastmcp.app/mcp

# Verify connection
curl https://SUKL-mcp.fastmcp.app/health
```

#### Option B: Local Development

```bash
# Clone repository
git clone https://github.com/DigiMedic/SUKL-mcp.git
cd SUKL-mcp

# Install with dev dependencies
pip install -e ".[dev]"

# Run local server
python -m sukl_mcp

# Test
pytest
```

### 🔧 Available Tools (8)

#### 1. `search_medicine`
Vyhledávání léků s fuzzy matching (tolerance překlepy).

**Parametry:**
- `query` (str): Název léku nebo aktivní látka
- `limit` (int, optional): Max počet výsledků (default: 10)

**Example:**
```python
await sukl_client.call_tool(
    "search_medicine",
    query="paralen",  # Najde "Paralen" i přes překlep
    limit=5
)
```

#### 2. `get_medicine_details`
Kompletní informace o léku včetně složení.

**Parametry:**
- `medicine_code` (str): Kód léku z SÚKL

**Returns:**
- Název, výrobce, forma, síla
- Aktivní látky a pomocné látky
- ATC klasifikace
- Registrační číslo

#### 3. `get_pil_content`
Příbalová informace (package insert) pro pacienty.

**Parametry:**
- `medicine_code` (str): Kód léku

**Returns:**
- Indikace, dávkování, kontraindikace
- Nežádoucí účinky
- Upozornění pro pacienty

#### 4. `get_spc_content`
Souhrn údajů o přípravku (SPC) pro zdravotníky.

**Parametry:**
- `medicine_code` (str): Kód léku

**Returns:**
- Farmakodynamické vlastnosti
- Farmakokinetika
- Klinická data
- Podrobné bezpečnostní informace

#### 5. `check_availability`
Kontrola dostupnosti + automatické doporučení alternativ.

**Parametry:**
- `medicine_code` (str): Kód léku

**Returns:**
- Dostupnost (ano/ne)
- Pokud ne: seznam alternativ se stejnou AL
- Multi-kriteriální ranking alternativ

#### 6. `get_reimbursement`
Informace o úhradách z veřejného zdravotního pojištění.

**Parametry:**
- `medicine_code` (str): Kód léku

**Returns:**
- Kategorie úhrady (A: 100%, B: částečná, D: bez úhrady)
- Předepisovatelnost (na lékařský předpis/volně)
- Cena pro pacienta (copay)

#### 7. `find_pharmacies`
Vyhledání lékáren podle lokace.

**Parametry:**
- `location` (str): Adresa nebo město
- `radius_km` (float, optional): Poloměr vyhledávání

#### 8. `get_atc_info`
Anatomicko-terapeuticko-chemická klasifikace (ATC).

**Parametry:**
- `atc_code` (str): ATC kód

**Returns:**
- Hierarchie ATC (kategorie, skupina, látka)
- České a anglické názvy
- Terapeutická skupina

### 🔌 Integration Pattern

```python
# src/agent/nodes/drug_agent.py
from typing import Dict, Any
from langgraph.runtime import Runtime
from agent.graph import State, Context

async def drug_agent_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Query SÚKL-mcp for drug information."""

    # Extract drug name from user query
    user_message = state.messages[-1].content
    drug_name = extract_drug_name(user_message)  # NER function

    # Get MCP client from runtime
    sukl_client = runtime.context.get("sukl_mcp_client")

    # Step 1: Search for drug
    search_results = await sukl_client.call_tool(
        "search_medicine",
        query=drug_name,
        limit=3
    )

    if not search_results:
        return {
            "messages": [{
                "role": "assistant",
                "content": f"Lék '{drug_name}' nebyl nalezen v databázi SÚKL."
            }],
            "next": "__end__"
        }

    # Step 2: Get details for top match
    top_match = search_results[0]
    details = await sukl_client.call_tool(
        "get_medicine_details",
        medicine_code=top_match["code"]
    )

    # Step 3: Get reimbursement info
    reimbursement = await sukl_client.call_tool(
        "get_reimbursement",
        medicine_code=top_match["code"]
    )

    # Step 4: Format response with citation
    response = format_drug_info(details, reimbursement)

    # Step 5: Add to retrieved_docs for citation system
    doc = Document(
        page_content=response,
        metadata={
            "source": "SÚKL",
            "medicine_code": top_match["code"],
            "timestamp": datetime.now().isoformat()
        }
    )

    return {
        "messages": [{
            "role": "assistant",
            "content": response
        }],
        "retrieved_docs": [doc],
        "next": "citation_system"
    }
```

### 🧪 Testing

```bash
# Unit test with mock SÚKL client
@pytest.mark.asyncio
async def test_drug_agent_with_mock_sukl():
    mock_client = MockSUKLClient()
    mock_client.add_response("search_medicine", [
        {"code": "12345", "name": "Paralen 500mg"}
    ])

    state = State(messages=[{"role": "user", "content": "Co je Paralen?"}])
    runtime = MockRuntime(context={"sukl_mcp_client": mock_client})

    result = await drug_agent_node(state, runtime)

    assert "Paralen" in result["messages"][0]["content"]
    assert len(result["retrieved_docs"]) == 1

# Integration test with real SÚKL server
@pytest.mark.integration
@pytest.mark.asyncio
async def test_drug_agent_with_real_sukl():
    sukl_client = SUKLMCPClient(url="https://SUKL-mcp.fastmcp.app/mcp")

    state = State(messages=[{"role": "user", "content": "Paralen 500mg"}])
    runtime = Runtime(context={"sukl_mcp_client": sukl_client})

    result = await drug_agent_node(state, runtime)

    assert result["messages"][0]["role"] == "assistant"
    assert len(result["retrieved_docs"]) > 0
```

---

## BioMCP Integration

### 🎯 Use Case

Agent potřebuje mezinárodní medicínské výzkumy a data:
- Vyhledání vědeckých článků v PubMed
- Klinické studie (ClinicalTrials.gov)
- Genetické varianty (MyVariant.info)
- Informace o genech, chorobách, lécích

### 📦 Repository

**GitHub**: https://github.com/genomoncology/biomcp
**Installation**: `pip install biomcp-python`

### 🛠️ Installation

#### Option A: Claude Desktop Integration

```bash
# 1. Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Configure Claude Desktop
# Edit ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "biomcp": {
      "command": "uv",
      "args": ["run", "--with", "biomcp-python", "biomcp", "run"]
    }
  }
}

# 3. Restart Claude Desktop
```

#### Option B: Python Package

```bash
# Install BioMCP
pip install biomcp-python

# Verify
biomcp --version
```

### 🔧 Available Tools (24)

#### Core Tools (3)

1. **`think`** - Sequential reasoning pro complex queries
2. **`search`** - Unified search across all domains
3. **`fetch`** - Retrieve complete entity details

#### Article Tools (4)

4. **`article_searcher`** - Search PubMed/PubTator3
5. **`article_getter`** - Get article details by PMID
6. **`article_recommender`** - Find similar articles
7. **`article_pmc_getter`** - Get full-text from PMC

#### Trial Tools (6)

8. **`trial_searcher`** - Search ClinicalTrials.gov
9. **`trial_getter`** - Get trial details by NCT ID
10. **`trial_nci_searcher`** - NCI-specific trial search
11. **`trial_nci_getter`** - NCI trial details
12. **`trial_nci_disease_searcher`** - Search by disease
13. **`trial_nci_intervention_searcher`** - Search by intervention

#### Variant Tools (3)

14. **`variant_searcher`** - Search genetic variants
15. **`variant_getter`** - Get variant details
16. **`variant_annotator`** - Annotate VCF files

#### Gene/Disease/Drug Tools (8)

17. **`gene_getter`** - Gene information
18. **`disease_getter`** - Disease details
19. **`drug_getter`** - Drug/compound info
20. **`tcga_getter`** - TCGA cancer genomics
21. **`gdc_getter`** - GDC data portal
22. **`cbioportal_getter`** - cBioPortal studies
23. **`oncokb_getter`** - OncoKB annotations
24. **`openfda_getter`** - FDA adverse events

### 🔌 Integration Pattern (Sandwich Pattern)

**Challenge**: BioMCP tools očekávají anglické queries, ale uživatelé píší česky.

**Solution**: Sandwich Pattern (CZ→EN→CZ)

```python
# src/agent/nodes/pubmed_agent.py
from langchain_openai import ChatOpenAI

async def pubmed_agent_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Query BioMCP for research articles with CZ→EN→CZ translation."""

    # Extract query from user message (CZ)
    user_query_cz = state.messages[-1].content

    # Step 1: Translate CZ → EN
    llm = ChatOpenAI(model="gpt-4o-mini")
    translation_prompt = f"""
    Translate this Czech medical query to English:
    "{user_query_cz}"

    Provide only the English translation, no explanation.
    """
    query_en = await llm.ainvoke(translation_prompt)

    # Step 2: Query BioMCP (EN)
    biomcp_client = runtime.context.get("biomcp_client")

    # Use think tool for complex reasoning
    think_result = await biomcp_client.call_tool(
        "think",
        goal=query_en.content,
        max_steps=5
    )

    # Use article_searcher
    articles = await biomcp_client.call_tool(
        "article_searcher",
        query=query_en.content,
        max_results=10
    )

    # Step 3: Translate results EN → CZ
    articles_cz = []
    for article in articles[:3]:  # Top 3 articles
        title_cz = await llm.ainvoke(f"Translate to Czech: {article['title']}")
        abstract_cz = await llm.ainvoke(f"Translate to Czech: {article['abstract']}")

        articles_cz.append({
            "title": title_cz.content,
            "abstract": abstract_cz.content,
            "pmid": article["pmid"],
            "authors": article["authors"],
            "journal": article["journal"]
        })

    # Step 4: Format response (CZ)
    response = format_articles(articles_cz)

    # Step 5: Create documents for citation
    docs = [
        Document(
            page_content=f"{art['title']}\n\n{art['abstract']}",
            metadata={
                "source": "PubMed",
                "pmid": art["pmid"],
                "journal": art["journal"]
            }
        )
        for art in articles_cz
    ]

    return {
        "messages": [{"role": "assistant", "content": response}],
        "retrieved_docs": docs,
        "next": "citation_system"
    }
```

### 🧪 Testing

```bash
# CLI testing
biomcp article search --gene BRAF --disease Melanoma
biomcp trial get NCT04280705 --detail all

# Python testing
import asyncio
from biomcp import BioMCPClient

async def test_biomcp():
    client = BioMCPClient()

    # Search articles
    results = await client.call_tool(
        "article_searcher",
        query="BRAF V600E melanoma",
        max_results=5
    )

    print(f"Found {len(results)} articles")
    for r in results:
        print(f"- {r['title']} (PMID: {r['pmid']})")

asyncio.run(test_biomcp())
```

---

## Development Setup

### Environment Configuration

Vytvořte `.env` file:

```bash
# LangSmith Tracing
LANGSMITH_API_KEY=lsv2_pt_your_key
LANGSMITH_PROJECT=czech-medai-dev
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# SÚKL-mcp
SUKL_MCP_URL=https://SUKL-mcp.fastmcp.app/mcp
SUKL_MCP_TRANSPORT=http
SUKL_MCP_TIMEOUT=30

# BioMCP
BIOMCP_TRANSPORT=stdio
BIOMCP_COMMAND=biomcp run
BIOMCP_TIMEOUT=60

# Translation (for Sandwich Pattern)
OPENAI_API_KEY=sk-...
TRANSLATION_MODEL=gpt-4o-mini

# Fallback Mode
ENABLE_MCP_FALLBACK=true
MCP_RETRY_ATTEMPTS=3
MCP_RETRY_DELAY=1.0

# Development
LOG_LEVEL=INFO
DEBUG_MCP=false
```

### MCP Client Wrappers

Create abstraction layer v `src/agent/mcp/`:

```python
# src/agent/mcp/sukl_client.py
import httpx
from typing import Dict, Any, Optional

class SUKLMCPClient:
    """Wrapper for SÚKL-mcp HTTP transport."""

    def __init__(self, url: str, timeout: int = 30):
        self.url = url
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def call_tool(
        self,
        tool_name: str,
        **params: Any
    ) -> Dict[str, Any]:
        """Call SÚKL MCP tool."""
        try:
            response = await self.client.post(
                f"{self.url}/tools/{tool_name}",
                json=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SÚKL MCP error: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if server is available."""
        try:
            response = await self.client.get(f"{self.url}/health")
            return response.status_code == 200
        except:
            return False
```

```python
# src/agent/mcp/biomcp_client.py
import subprocess
import json
from typing import Dict, Any

class BioMCPClient:
    """Wrapper for BioMCP STDIO transport."""

    def __init__(self, command: str = "biomcp run"):
        self.command = command

    async def call_tool(
        self,
        tool_name: str,
        **params: Any
    ) -> Dict[str, Any]:
        """Call BioMCP tool via stdio."""
        request = {
            "jsonrpc": "2.0",
            "method": f"tools/{tool_name}",
            "params": params,
            "id": 1
        }

        process = await asyncio.create_subprocess_exec(
            *self.command.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout, stderr = await process.communicate(
            input=json.dumps(request).encode()
        )

        if process.returncode != 0:
            raise RuntimeError(f"BioMCP error: {stderr.decode()}")

        response = json.loads(stdout.decode())
        return response.get("result", {})
```

### Context Initialization

```python
# src/agent/graph.py
from agent.mcp.sukl_client import SUKLMCPClient
from agent.mcp.biomcp_client import BioMCPClient
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize MCP clients
async def initialize_mcp_clients() -> Dict[str, Any]:
    """Initialize all MCP clients."""
    clients = {}

    # SÚKL-mcp
    sukl_url = os.getenv("SUKL_MCP_URL")
    if sukl_url:
        sukl_client = SUKLMCPClient(url=sukl_url)
        if await sukl_client.health_check():
            clients["sukl_mcp_client"] = sukl_client
            logger.info("SÚKL-mcp client initialized")
        else:
            logger.warning("SÚKL-mcp server unavailable")

    # BioMCP
    biomcp_cmd = os.getenv("BIOMCP_COMMAND", "biomcp run")
    try:
        clients["biomcp_client"] = BioMCPClient(command=biomcp_cmd)
        logger.info("BioMCP client initialized")
    except Exception as e:
        logger.warning(f"BioMCP initialization failed: {e}")

    return clients

# Use in graph invocation
async def invoke_graph(messages, user_context=None):
    """Invoke graph with MCP clients in context."""
    mcp_clients = await initialize_mcp_clients()

    context = {
        "model_name": "claude-sonnet-4",
        "temperature": 0.0,
        **mcp_clients,
        **(user_context or {})
    }

    return await graph.ainvoke(
        {"messages": messages},
        context=context
    )
```

---

## Testing MCP Connections

### Health Checks

```bash
# Test SÚKL-mcp
curl https://SUKL-mcp.fastmcp.app/health

# Test BioMCP CLI
biomcp --version
biomcp article search --query "test" --max_results 1
```

### Integration Tests

```python
# tests/integration_tests/test_mcp_integration.py
import pytest
from agent.mcp.sukl_client import SUKLMCPClient
from agent.mcp.biomcp_client import BioMCPClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_sukl_search_medicine():
    """Test SÚKL-mcp search_medicine tool."""
    client = SUKLMCPClient(url="https://SUKL-mcp.fastmcp.app/mcp")

    result = await client.call_tool(
        "search_medicine",
        query="Paralen",
        limit=5
    )

    assert len(result) > 0
    assert "Paralen" in result[0]["name"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_biomcp_article_search():
    """Test BioMCP article_searcher tool."""
    client = BioMCPClient()

    result = await client.call_tool(
        "article_searcher",
        query="diabetes mellitus",
        max_results=3
    )

    assert len(result) == 3
    assert "pmid" in result[0]
```

---

## Architecture Patterns

### Pattern 1: MCP Tool Chaining

```python
async def drug_agent_with_alternatives(state, runtime):
    """Chain SÚKL tools: search → details → availability → alternatives."""
    sukl = runtime.context["sukl_mcp_client"]

    # 1. Search
    search = await sukl.call_tool("search_medicine", query="Ibuprofen")
    drug = search[0]

    # 2. Details
    details = await sukl.call_tool("get_medicine_details", medicine_code=drug["code"])

    # 3. Check availability
    avail = await sukl.call_tool("check_availability", medicine_code=drug["code"])

    # 4. If unavailable, get alternatives
    if not avail["available"]:
        alternatives = avail["alternatives"]
        # Format response with alternatives

    return format_response(details, alternatives)
```

### Pattern 2: Parallel MCP Calls

```python
async def supervisor_multi_source(state, runtime):
    """Query multiple MCP sources in parallel."""
    sukl = runtime.context["sukl_mcp_client"]
    biomcp = runtime.context["biomcp_client"]

    # Parallel execution
    sukl_task = sukl.call_tool("search_medicine", query="BRAF inhibitor")
    biomcp_task = biomcp.call_tool("article_searcher", query="BRAF melanoma")

    sukl_result, biomcp_result = await asyncio.gather(
        sukl_task,
        biomcp_task,
        return_exceptions=True
    )

    # Combine results
    return combine_sources(sukl_result, biomcp_result)
```

### Pattern 3: Fallback Strategy

```python
async def robust_mcp_call(client, tool, fallback_data=None, **params):
    """Call MCP tool with retry and fallback."""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            return await client.call_tool(tool, **params)
        except Exception as e:
            logger.warning(f"MCP call failed (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                if fallback_data:
                    logger.info("Using fallback data")
                    return fallback_data
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

## Troubleshooting

### SÚKL-mcp Issues

**Problem**: Connection timeout

```bash
# Check server status
curl -v https://SUKL-mcp.fastmcp.app/health

# Test with increased timeout
export SUKL_MCP_TIMEOUT=60
```

**Problem**: Invalid medicine code

```python
# Always search first to get valid codes
search = await sukl.call_tool("search_medicine", query="Paralen")
code = search[0]["code"]  # Use this code
```

### BioMCP Issues

**Problem**: stdio transport not working

```bash
# Check BioMCP installation
which biomcp
biomcp --version

# Test CLI directly
biomcp article search --query "test"

# Try HTTP transport instead
export BIOMCP_TRANSPORT=http
export BIOMCP_URL=http://localhost:8080
```

**Problem**: Translation costs too high

```python
# Cache translations
from functools import lru_cache

@lru_cache(maxsize=1000)
async def translate_cached(text: str, direction: str):
    return await translate(text, direction)
```

### General MCP Issues

**Problem**: Tools not discovered

```python
# List available tools
print(await client.list_tools())
```

**Problem**: Response parsing errors

```python
# Validate response schema
from pydantic import BaseModel

class ArticleResponse(BaseModel):
    pmid: str
    title: str
    abstract: str

# Use in validation
response = ArticleResponse(**result)
```

---

## Next Steps

1. **Feature 002-mcp-infrastructure**:
   - Implement MCP client wrappers
   - Setup health checks
   - Error handling & retry logic

2. **Feature 003-sukl-drug-agent**:
   - Integrate SÚKL-mcp tools
   - NER for drug names
   - Czech response formatting

3. **Feature 005-biomcp-pubmed-agent**:
   - Implement Sandwich Pattern
   - Translation caching
   - Citation extraction

---

**Version**: 1.0.0
**Last Updated**: 2026-01-14
**Maintainer**: Czech MedAI Team
