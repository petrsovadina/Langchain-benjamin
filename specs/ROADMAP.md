# Czech MedAI (Benjamin) - Feature Roadmap

**Project**: LangGraph-based AI Assistant for Czech Physicians
**Constitution**: v1.0.1
**Generated**: 2026-01-13

---

## 📊 Feature Decomposition Strategy

Tento projekt jsme rozložili na **12 featur** organizovaných do **4 fází** podle závislostí a priorit z PRD dokumentace.

### Strategie rozkladu:
1. **Phase 0: Foundation** - Infrastruktura a základní LangGraph setup
2. **Phase 1: Core Agents** - Implementace 4 specializovaných agentů
3. **Phase 2: Integration** - Supervisor orchestrace a citační systém
4. **Phase 3: UX & Deployment** - Frontend a production readiness

---

## 🏗️ Phase 0: Foundation (Týden 1-2)

### 001-langgraph-foundation
**Priority**: P0 (CRITICAL - blocking all)
**Branch**: `001-langgraph-foundation`
**Estimate**: 5 days

**Scope**:
- Setup LangGraph State schema (`AgentState` TypedDict)
- Implement basic `Context` configuration
- Configure pytest fixtures for graph testing
- Setup LangSmith tracing integration
- Create base graph structure in `src/agent/graph.py`

**PRD References**: 
- MVP Spec §3.1 (Architecture)
- Tech Doc §2.1 (State Schema)

**Constitution Check**:
- ✅ Principle I: Graph-centric (core graph setup)
- ✅ Principle II: Type safety (State/Context typing)
- ✅ Principle III: Test-first (pytest fixtures)
- ✅ Principle IV: Observability (LangSmith)

---

### 002-mcp-infrastructure
**Priority**: P0 (CRITICAL - blocking agents)
**Branch**: `002-mcp-infrastructure`
**Estimate**: 4 days

**Scope**:
- Setup MCP protocol base classes
- Configure Docker network for BioMCP integration
- Create MCP client wrapper utilities
- Implement health check endpoints for MCP servers
- Setup Supabase connection with pgvector extension

**PRD References**:
- Architecture Doc §3 (MCP Strategy)
- Infrastructure §4 (Docker Network)

**Dependencies**: None (parallel with 001)

---

## 🤖 Phase 1: Core Agents (Týden 3-6)

### 003-sukl-drug-agent
**Priority**: P0 (Must Have - US-004)
**Branch**: `003-sukl-drug-agent`
**Estimate**: 8 days

**Scope**:
- Build `agent_local` node for drug queries
- Implement SÚKL vector search (pgvector + embeddings)
- Create tools: `search_drugs`, `get_drug_details`, `get_spc`
- Parse SÚKL OpenData CSV (Windows-1250 encoding)
- Vector indexing for ~100k drug records
- Unit tests for drug search accuracy

**PRD References**:
- MVP Spec §4.2 (Drug Agent)
- User Stories: US-004
- Functional Req: F-001, F-004

**Dependencies**: 001, 002

---

### 004-vzp-pricing-agent
**Priority**: P1 (Should Have - US-005, US-006)
**Branch**: `004-vzp-pricing-agent`
**Estimate**: 6 days

**Scope**:
- Build `agent_pricing` node
- Implement VZP LEK-13 parser (exact search, no vectors)
- Create tools: `get_pricing`, `find_alternatives`
- Monthly data update automation
- Unit tests for pricing accuracy
- Alternative drug suggestions logic

**PRD References**:
- MVP Spec §4.4 (Pricing Agent)
- User Stories: US-005, US-006
- Functional Req: F-005

**Dependencies**: 003 (shares SÚKL codes)

---

### 005-biomcp-pubmed-agent
**Priority**: P0 (Must Have - US-001)
**Branch**: `005-biomcp-pubmed-agent`
**Estimate**: 7 days

**Scope**:
- Build `agent_research` node
- Integrate BioMCP Docker container (article_searcher)
- Implement "Sandwich Pattern" (CZ→EN→CZ translation)
- Create tools: `search_pubmed`, `get_abstract`
- Citation extraction (PMID/DOI)
- MeSH term query expansion
- Unit tests for translation & retrieval

**PRD References**:
- Architecture Doc §3.B (Global Layer)
- MVP Spec §4.3 (PubMed Agent)
- User Stories: US-001

**Dependencies**: 002 (MCP infrastructure)

---

### 006-guidelines-agent
**Priority**: P1 (Should Have - post-MVP consideration)
**Branch**: `006-guidelines-agent`
**Estimate**: 8 days

**Scope**:
- Build `agent_guidelines` node
- PDF ingestion pipeline for ČLS JEP guidelines
- Vector embeddings for guideline sections
- Create tools: `search_guidelines`, `get_guideline_section`
- Semantic chunking strategy
- Citation with guideline IDs
- Unit tests for guideline retrieval

**PRD References**:
- MVP Spec §4.5 (Guidelines Agent)
- User Stories: US-003

**Dependencies**: 001, 002 (can run parallel with 003-005)

---

## 🔄 Phase 2: Integration (Týden 7-9)

### 007-supervisor-orchestration
**Priority**: P0 (CRITICAL - core routing)
**Branch**: `007-supervisor-orchestration`
**Estimate**: 9 days

**Scope**:
- Implement `supervisor_node` with Claude function calling
- Build intent classifier (8 intent types)
- Multi-agent routing logic (single & compound queries)
- Conditional edges based on intent
- Query delegation to specialized agents
- Fallback handling for unavailable agents
- Integration tests for routing accuracy

**PRD References**:
- Architecture Doc §2.2 (Supervisor Node)
- MVP Spec §5 (Query Classification)
- Functional Req: F-002

**Dependencies**: 003, 004, 005, 006 (requires all agents ready)

---

### 008-citation-system
**Priority**: P0 (Must Have - US-002)
**Branch**: `008-citation-system`
**Estimate**: 6 days

**Scope**:
- Unified Citation schema for all sources
- Inline citation insertion `[1][2][3]`
- Reference list generation at response end
- Citation link formatting (PMID, SÚKL, DOI, ČLS JEP)
- Citation deduplication logic
- Integration tests for citation accuracy

**PRD References**:
- Functional Req: F-003
- User Stories: US-002

**Dependencies**: 007 (requires synthesized responses)

---

### 009-synthesizer-node
**Priority**: P0 (Must Have - final output)
**Branch**: `009-synthesizer-node`
**Estimate**: 5 days

**Scope**:
- Implement `synthesizer_node` (final response generation)
- Combine multi-agent outputs into coherent answer
- Apply citation system
- Czech medical terminology validation
- Response formatting (3-5 sentences for QuickConsult)
- Confidence scoring
- Integration tests for synthesis quality

**PRD References**:
- Architecture Doc §5 (Data Flow)
- Functional Req: F-001

**Dependencies**: 007, 008

---

## 🎨 Phase 3: UX & Deployment (Týden 10-12)

### 010-czech-localization
**Priority**: P0 (Must Have - US-003)
**Branch**: `010-czech-localization`
**Estimate**: 4 days

**Scope**:
- Czech UI strings and error messages
- Medical abbreviations dictionary (80+ terms)
- Term glossary with first-mention explanations
- Czech medical terminology validation rules
- Unit tests for abbreviation expansion

**PRD References**:
- Functional Req: F-004
- User Stories: US-003

**Dependencies**: 009 (applies to final output)

---

### 011-fastapi-backend
**Priority**: P0 (Must Have - API layer)
**Branch**: `011-fastapi-backend`
**Estimate**: 6 days

**Scope**:
- FastAPI server setup with SSE streaming
- REST endpoints for graph invocation
- Health check endpoints for all MCP servers
- Request/response validation with Pydantic
- Error handling and logging
- OpenAPI documentation
- Integration tests for API layer

**PRD References**:
- Tech Stack (FastAPI)
- Infrastructure Doc §4

**Dependencies**: 009 (requires complete graph)

---

### 012-nextjs-frontend
**Priority**: P0 (Must Have - user interface)
**Branch**: `012-nextjs-frontend`
**Estimate**: 10 days

**Scope**:
- Next.js 14 app with TypeScript
- Chat interface with streaming responses
- Citation badge components
- Czech medical UI (Radix UI + Tailwind)
- Loading states and error handling
- Mobile responsive design
- E2E tests with Playwright

**PRD References**:
- Component Spec: Frontend UX Design
- Tech Stack (Next.js 14.x)

**Dependencies**: 011 (requires API endpoints)

---

## 📈 Feature Dependency Graph

```
Phase 0:
  001-langgraph-foundation  ──┐
  002-mcp-infrastructure    ──┼──┐
                              │  │
Phase 1:                      │  │
  003-sukl-drug-agent     ────┤  │
  004-vzp-pricing-agent   ────┘  │
  005-biomcp-pubmed-agent ───────┤
  006-guidelines-agent    ───────┘
                              │
Phase 2:                      │
  007-supervisor-orchestration ──┤
  008-citation-system        ────┤
  009-synthesizer-node       ────┘
                              │
Phase 3:                      │
  010-czech-localization     ────┤
  011-fastapi-backend        ────┤
  012-nextjs-frontend        ────┘
```

---

## 🎯 MVP Completion Criteria

**Minimum features for MVP launch**:
- ✅ Features 001-005 (Foundation + Drug/Pricing/PubMed agents)
- ✅ Features 007-009 (Orchestration + Citations + Synthesis)
- ✅ Features 010-012 (Localization + Backend + Frontend)

**Optional for MVP** (can defer to v1.1):
- ⚠️ Feature 006 (Guidelines Agent) - can launch without ČLS JEP integration

---

## 📝 Next Steps

### 1. Create Feature Branches
```bash
# Start with foundation
git checkout -b 001-langgraph-foundation
git checkout -b 002-mcp-infrastructure
```

### 2. Run Spec Kit Workflow for Each Feature
```bash
# For each feature branch:
/speckit.specify [popis z roadmap scope]
/speckit.plan [technické detaily]
/speckit.tasks
/speckit.implement
```

### 3. Track Progress
- Update this ROADMAP.md as features complete
- Link PRD documents to respective `specs/###-feature/spec.md`
- Maintain constitution compliance checklist

---

## 🔗 Related Documents

- [Constitution v1.0.1](../.specify/memory/constitution.md)
- [PRD Documentation](../PRD-docs/)
- [MVP Specification](../PRD-docs/04-specifikace-komponent/01-mvp-specifikace.md)
- [Architecture Analysis](../PRD-docs/03-architektura-a-technicka-dokumentace/01-architektura-hlubkova-analyza.md)

---

**Status**: Ready for implementation
**Next Action**: Create branch `001-langgraph-foundation` and run `/speckit.specify`
