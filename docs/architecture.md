# Czech MedAI - Architecture Documentation

**Version**: 0.1.0 | **Last Updated**: 2026-02-15

## System Overview

Czech MedAI is a multi-agent AI assistant for Czech physicians, built on
LangGraph with a Next.js frontend and FastAPI bridge layer. The system provides
clinical decision support integrating SUKL, PubMed, and CLS JEP sources with
inline citations.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI["Next.js 14<br/>(React 18, TypeScript)"]
        SSEClient["SSE Client<br/>(lib/api.ts)"]
        Hooks["useConsult Hook<br/>(auto-retry, state)"]
    end

    subgraph "API Layer (FastAPI :8000)"
        Gateway["FastAPI App<br/>(CORS, Rate Limit, Security Headers)"]
        Routes["/api/v1/consult<br/>SSE StreamingResponse"]
        Health["/health<br/>Component Status"]
        Cache["Redis Cache<br/>(quick mode only)"]
    end

    subgraph "Agent Layer (LangGraph)"
        Supervisor["Supervisor Node<br/>(LLM Intent Classification)"]
        DrugAgent["Drug Agent<br/>(SUKL MCP)"]
        PubMedAgent["PubMed Agent<br/>(BioMCP, CZ->EN)"]
        GuidelinesAgent["Guidelines Agent<br/>(pgvector Search)"]
        GeneralAgent["General Agent<br/>(Claude LLM)"]
        Synthesizer["Synthesizer Node<br/>(Citation Merge)"]
    end

    subgraph "External Services"
        SUKL["SUKL MCP Server<br/>(JSON-RPC 2.0)"]
        BioMCP["BioMCP Server<br/>(REST, Docker)"]
        PGVector["PostgreSQL + pgvector<br/>(Guidelines DB)"]
        Redis["Redis 7<br/>(Response Cache)"]
        LangSmith["LangSmith<br/>(Tracing)"]
    end

    UI --> SSEClient
    SSEClient --> Hooks
    Hooks --> Gateway
    Gateway --> Routes
    Gateway --> Health
    Routes --> Cache
    Routes --> Supervisor
    Supervisor -->|"Send API"| DrugAgent
    Supervisor -->|"Send API"| PubMedAgent
    Supervisor -->|"Send API"| GuidelinesAgent
    Supervisor -->|"Send API"| GeneralAgent
    DrugAgent --> Synthesizer
    PubMedAgent --> Synthesizer
    GuidelinesAgent --> Synthesizer
    GeneralAgent --> Synthesizer
    DrugAgent --> SUKL
    PubMedAgent --> BioMCP
    GuidelinesAgent --> PGVector
    Cache --> Redis
    Supervisor --> LangSmith
```

## LangGraph Agent Flow

```mermaid
graph LR
    Start(("__start__")) --> Supervisor
    Supervisor -->|"Send API<br/>(parallel dispatch)"| DrugAgent["drug_agent"]
    Supervisor -->|"Send API"| PubMedAgent["pubmed_agent"]
    Supervisor -->|"Send API"| GuidelinesAgent["guidelines_agent"]
    Supervisor -->|"Send API"| GeneralAgent["general_agent"]
    DrugAgent --> Synthesizer["synthesizer"]
    PubMedAgent --> Synthesizer
    GuidelinesAgent --> Synthesizer
    GeneralAgent --> Synthesizer
    Synthesizer --> End(("__end__"))
```

### Routing Decision Flow

```mermaid
flowchart TD
    Query["User Query"] --> ExplicitCheck{"Explicit query<br/>in State?"}
    ExplicitCheck -->|"drug_query"| Drug["drug_agent"]
    ExplicitCheck -->|"research_query"| PubMed["pubmed_agent"]
    ExplicitCheck -->|"guideline_query"| Guidelines["guidelines_agent"]
    ExplicitCheck -->|"None"| LLMClassify["LLM Intent<br/>Classification"]

    LLMClassify -->|"Success"| Validate["Validate agents<br/>+ MCP availability"]
    LLMClassify -->|"Failure"| KeywordFallback["Keyword Routing<br/>(fallback_to_keyword_routing)"]

    KeywordFallback -->|"Drug keywords"| Drug
    KeywordFallback -->|"Research keywords"| PubMed
    KeywordFallback -->|"Guidelines keywords"| Guidelines
    KeywordFallback -->|"No match"| General["general_agent"]

    Validate --> SendAPI["Send API<br/>(single or parallel)"]
    SendAPI --> Drug
    SendAPI --> PubMed
    SendAPI --> Guidelines
    SendAPI --> General
```

## Data Flow: Consult Request

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant API as FastAPI
    participant Cache as Redis
    participant Graph as LangGraph
    participant Sup as Supervisor
    participant Agent as Agent(s)
    participant Synth as Synthesizer
    participant MCP as MCP Server

    FE->>API: POST /api/v1/consult (SSE)
    API->>Cache: Check cache (quick mode)
    alt Cache Hit
        Cache-->>API: Cached response
        API-->>FE: SSE: cache_hit + final + done
    else Cache Miss
        API->>Graph: astream_events()
        Graph->>Sup: supervisor_node(state, runtime)
        Sup->>Sup: LLM classify intent
        Sup-->>Graph: Send("agent_name", state)

        Graph-->>FE: SSE: agent_start

        Graph->>Agent: agent_node(state, runtime)
        Agent->>MCP: call_tool(name, params)
        MCP-->>Agent: MCP response
        Agent-->>Graph: {messages, retrieved_docs}

        Graph-->>FE: SSE: agent_complete

        Graph->>Synth: synthesizer_node(state, runtime)
        Synth->>Synth: Extract citations
        Synth->>Synth: Renumber globally
        Synth->>Synth: LLM synthesis (multi-agent)
        Synth->>Synth: Validate Czech terminology
        Synth-->>Graph: {messages, retrieved_docs}

        Graph-->>API: Final state
        API->>Cache: Cache response (quick mode)
        API-->>FE: SSE: final + done
    end
```

## Component Details

### State Schema

```python
@dataclass
class State:
    messages: Annotated[list[AnyMessage], add_messages]
    next: Annotated[str, _keep_last] = "__end__"
    retrieved_docs: Annotated[list[Document], add_documents] = field(
        default_factory=list
    )
    drug_query: DrugQuery | None = None
    research_query: ResearchQuery | None = None
    guideline_query: GuidelineQuery | None = None
```

### Context Schema

```python
class Context(TypedDict, total=False):
    model_name: str              # default: claude-sonnet-4-5-20250929
    temperature: float           # default: 0.0
    langsmith_project: str
    user_id: str | None
    sukl_mcp_client: Any         # SUKLMCPClient
    biomcp_client: Any           # BioMCPClient
    openai_api_key: str          # for guidelines embeddings
    conversation_context: Any
    mode: Literal["quick", "deep"]
```

### Agent Nodes

| Node | Module | Responsibility | External Dependency |
|------|--------|---------------|-------------------|
| `supervisor` | `nodes/supervisor.py` | Intent classification, routing | Anthropic API |
| `drug_agent` | `nodes/drug_agent.py` | Czech pharmaceutical DB queries | SUKL MCP (JSON-RPC) |
| `pubmed_agent` | `nodes/pubmed_agent.py` | Biomedical research with CZ->EN | BioMCP (REST) |
| `guidelines_agent` | `nodes/guidelines_agent.py` | Clinical guideline search | PostgreSQL + pgvector |
| `general_agent` | `nodes/general_agent.py` | General medical Q&A | Anthropic API |
| `synthesizer` | `nodes/synthesizer.py` | Response merge, citations, terminology | Anthropic API |

### MCP Protocol Architecture

```mermaid
graph LR
    subgraph "Application Layer"
        DrugNode["drug_agent_node"]
        PubMedNode["pubmed_agent_node"]
    end

    subgraph "Adapter Layer"
        SUKLClient["SUKLMCPClient<br/>(JSON-RPC 2.0)"]
        BioClient["BioMCPClient<br/>(REST)"]
    end

    subgraph "Port Layer"
        Interface["IMCPClient<br/>(Interface)"]
    end

    subgraph "External"
        SUKLServer["SUKL MCP Server<br/>9 tools"]
        BioServer["BioMCP Docker<br/>24 tools"]
    end

    DrugNode --> SUKLClient
    PubMedNode --> BioClient
    SUKLClient -.->|implements| Interface
    BioClient -.->|implements| Interface
    SUKLClient -->|"JSON-RPC<br/>tools/call"| SUKLServer
    BioClient -->|"REST<br/>/tools/{name}"| BioServer
```

## Infrastructure

### Docker Compose Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `api` | Custom (Dockerfile) | 8000 | FastAPI + LangGraph (4 uvicorn workers) |
| `redis` | redis:7-alpine | 6379 | Response cache (256MB, allkeys-lru) |
| `postgres` | ankane/pgvector | 5432 | Guidelines DB (semantic search) |

### Middleware Stack

```
Request
  -> Request ID (UUID v4, X-Request-ID header)
  -> Security Headers (HSTS, CSP, X-Frame-Options: DENY, nosniff)
  -> Process Time (X-Process-Time header)
  -> CORS (configurable origins)
  -> Rate Limiting (10 req/min per IP, slowapi)
  -> Route Handler
Response
```

### Security Measures

| Layer | Protection |
|-------|-----------|
| Input | SQL injection regex, XSS pattern blocking, 1000 char limit |
| Transport | HSTS, CSP, X-Frame-Options: DENY |
| Rate Limiting | 10 req/min per IP (slowapi) |
| Request Tracking | UUID per request (X-Request-ID) |
| MCP Clients | Content size limits (1MB total, 100KB per field) |
| Regex | Line-anchored patterns (ReDoS prevention) |
| Concurrency | Thread-safe ID generation (itertools.count) |
| Resources | Async context managers, 30s timeouts |

## Directory Structure

```
Langchain-benjamin/
├── frontend/                    # Next.js 14 (TypeScript)
│   ├── app/                     # App Router pages
│   │   ├── page.tsx             # Main chat interface
│   │   └── globals.css          # OKLCH design tokens
│   ├── components/              # React components (14 total)
│   │   ├── Omnibox.tsx          # Medical query input
│   │   ├── CitedResponse.tsx    # Response with inline citations
│   │   └── CitationBadge.tsx    # Citation [N] with HoverCard
│   ├── hooks/                   # Custom React hooks
│   │   ├── useConsult.ts        # API integration + retry
│   │   └── useRetry.ts          # Exponential backoff
│   ├── lib/                     # Utilities
│   │   ├── api.ts               # SSE streaming client
│   │   └── citations.ts         # Citation parsing
│   └── __tests__/               # Vitest + RTL + jest-axe
│
├── langgraph-app/               # Backend
│   ├── src/
│   │   ├── agent/
│   │   │   ├── graph.py         # State, Context, graph compilation
│   │   │   ├── nodes/           # Agent node modules
│   │   │   │   ├── supervisor.py
│   │   │   │   ├── drug_agent.py
│   │   │   │   ├── pubmed_agent.py
│   │   │   │   ├── guidelines_agent.py
│   │   │   │   ├── general_agent.py
│   │   │   │   ├── synthesizer.py
│   │   │   │   └── supervisor_prompts.py
│   │   │   ├── models/          # Pydantic models
│   │   │   ├── mcp/             # MCP client adapters
│   │   │   │   ├── adapters/    # SUKLMCPClient, BioMCPClient
│   │   │   │   └── domain/      # Ports, entities, exceptions
│   │   │   └── utils/           # Helpers (timeout, message, storage)
│   │   └── api/                 # FastAPI bridge
│   │       ├── main.py          # App, middleware, lifespan
│   │       ├── routes.py        # Endpoints (/health, /consult)
│   │       ├── schemas.py       # Request/response models
│   │       └── config.py        # Pydantic Settings
│   ├── tests/
│   │   ├── unit_tests/          # 442 tests
│   │   ├── integration_tests/
│   │   ├── quality/
│   │   └── conftest.py
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── langgraph.json
│
├── docs/                        # Generated documentation
├── specs/                       # Feature specifications
│   └── ROADMAP.md
└── .specify/                    # SpecKit configuration
    └── memory/constitution.md   # Project constitution v1.1.2
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Orchestration | LangGraph (not LangChain chains) | Visual debugging, state management, parallel execution |
| Routing | Send API (not conditional edges) | Dynamic multi-agent dispatch, parallel execution |
| Frontend-Backend | SSE (not WebSocket) | Simpler protocol, unidirectional streaming sufficient |
| MCP Protocol | Per-server (JSON-RPC / REST) | Adapts to each server's native protocol |
| Caching | Redis (quick mode only) | Fast response for repeated queries |
| Guidelines DB | pgvector (not Pinecone/Weaviate) | Self-hosted, Docker-native, cost-effective |
| Keyword Routing | Single function (DRY) | `fallback_to_keyword_routing()` is the canonical source |
| Node Structure | Separate modules per agent | Independent testing, clear ownership (Principle V) |
