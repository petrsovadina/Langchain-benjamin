# BioAgents Architectural Patterns - Inspirace pro Czech MedAI

Tento dokument mapuje klíčové architektonické vzory z projektu [BioAgents](https://github.com/bio-xyz/BioAgents) a jejich adaptaci pro Czech MedAI.

## 📊 Přehled BioAgents

**BioAgents** je pokročilý AI framework pro autonomní vědecký výzkum v biologických vědách, kombinující multi-agent orchestraci s analýzou literatury a iterativním výzkumem.

**Tech Stack**: Bun runtime, TypeScript, PLpgSQL, Preact UI
**Repository**: https://github.com/bio-xyz/BioAgents

---

## 🎯 Klíčové Architektonické Vzory

### 1. Dual Workflow Pattern (Chat vs Deep Research)

#### BioAgents Approach:

```
Chat Route (/api/chat):
- Quick answers
- Single iteration
- Automatic literature integration
- Concise responses

Deep Research Route (/api/deep-research):
- Iterative investigation
- Hypothesis-driven
- Multi-iteration refinement
- Detailed analysis with citations
```

#### Adaptace pro Czech MedAI:

```
Quick Answer Mode:
User Query (CZ)
    ↓
[Supervisor] → Intent classification
    ↓
[Single Agent] → One-shot answer
    ↓
[Citation] → Add references
    ↓
Response (CZ) [1][2][3]

Deep Analysis Mode:
User Query (CZ)
    ↓
[Planning Agent] → Generate research tasks
    ↓
[Multiple Agents] → Parallel execution
    ├─→ SÚKL-mcp
    ├─→ BioMCP
    ├─→ Guidelines
    └─→ VZP pricing
    ↓
[Hypothesis Agent] → Synthesize findings
    ↓
[Reflection Agent] → Extract insights
    ↓
[User Feedback] → Refine or conclude
    ↓
Response (CZ) with full analysis
```

**Implementation**: Feature **013-workflow-modes** (Nová feature!)

**Benefits**:
- ✅ Quick answers pro simple queries (90% případů)
- ✅ Deep analysis pro complex clinical decisions (10% případů)
- ✅ User-controlled depth of investigation

---

### 2. State Management Architecture

#### BioAgents Approach:

```typescript
// Message State (ephemeral)
interface MessageState {
  fileBuffers?: Buffer[];
  tempProcessing?: any;
  // Cleared after message processing
}

// Conversation State (persistent)
interface ConversationState {
  uploadedDatasets: Dataset[];
  taskCompletionRecords: Task[];
  keyInsights: Insight[];
  currentHypotheses: Hypothesis[];
  researchObjectives: string[];
  // Stored in database
}
```

#### Adaptace pro Czech MedAI:

```python
# Message State (ephemeral - LangGraph State)
class MessageState(TypedDict):
    """Ephemeral state for single message processing."""
    messages: Annotated[list[AnyMessage], add_messages]
    next: str  # Routing control
    temp_docs: list[Document]  # Temporary retrieved docs
    processing_metadata: Dict[str, Any]  # Debug info

# Conversation State (persistent - Database)
@dataclass
class ConversationContext:
    """Persistent state across conversation."""
    conversation_id: str
    user_id: str

    # Medical context
    patient_context: Optional[PatientContext]
    previous_queries: list[str]

    # Knowledge accumulation
    retrieved_medicines: list[Medicine]
    cited_studies: list[Citation]
    clinical_insights: list[Insight]

    # Research tracking
    active_hypotheses: list[Hypothesis]
    research_objectives: list[str]
    task_history: list[Task]

    # Metadata
    created_at: datetime
    updated_at: datetime

# Runtime Context (configuration - LangGraph Context)
class Context(TypedDict, total=False):
    """Runtime configuration."""
    model_name: str
    temperature: float
    langsmith_project: str

    # MCP clients
    sukl_mcp_client: SUKLMCPClient
    biomcp_client: BioMCPClient

    # Conversation tracking
    conversation_context: ConversationContext

    # Workflow mode
    mode: Literal["quick", "deep"]
```

**Implementation**: Update Feature **001-langgraph-foundation**

**Benefits**:
- ✅ Clear separation: ephemeral vs persistent
- ✅ Conversation continuity across sessions
- ✅ Patient context preservation
- ✅ Research history tracking

---

### 3. Multi-Backend Knowledge Search Pattern

#### BioAgents Approach:

```
Literature Agent integrates 3 backends:
├─→ OPENSCHOLAR: High-quality scientific citations
├─→ EDISON: Advanced research mode
└─→ KNOWLEDGE: Custom vector DB + semantic search
```

#### Adaptace pro Czech MedAI:

```
Knowledge Search v Czech MedAI:
├─→ SÚKL-mcp: Czech pharmaceutical DB (68k+ drugs)
├─→ BioMCP: International research (PubMed, trials)
├─→ VZP LEK-13: Czech pricing database
├─→ Custom Knowledge: ČLS JEP guidelines (pgvector)
└─→ Cohere Reranking: Optional result optimization
```

**Implementation**: Feature **014-knowledge-orchestration** (Nová feature!)

**Pattern**:
```python
async def knowledge_orchestrator(
    query: str,
    sources: list[str] = ["sukl", "biomcp", "guidelines"]
) -> list[Document]:
    """Orchestrate multi-source knowledge search."""

    # Parallel search across backends
    tasks = []
    if "sukl" in sources:
        tasks.append(search_sukl(query))
    if "biomcp" in sources:
        tasks.append(search_biomcp(translate_cz_to_en(query)))
    if "guidelines" in sources:
        tasks.append(search_guidelines_vector(query))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge and deduplicate
    all_docs = merge_results(results)

    # Optional: Cohere reranking
    if use_reranking:
        all_docs = await rerank_with_cohere(query, all_docs)

    return all_docs[:top_k]
```

---

### 4. Hypothesis-Driven Research Pattern

#### BioAgents Approach:

```
Hypothesis Agent:
1. Analyze findings from multiple sources
2. Generate testable hypotheses
3. Maintain inline citations [1][2][3]
4. Update hypotheses based on new data
5. Track hypothesis evolution over iterations
```

#### Adaptace pro Czech MedAI:

```python
@dataclass
class ClinicalHypothesis:
    """Medical hypothesis with evidence."""
    hypothesis_text: str
    confidence: float  # 0.0-1.0
    supporting_evidence: list[Citation]
    contradicting_evidence: list[Citation]
    clinical_relevance: str
    safety_considerations: list[str]
    created_at: datetime
    refined_at: Optional[datetime]

async def hypothesis_agent_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Generate clinical hypotheses from evidence."""

    # Extract evidence from retrieved docs
    evidence = extract_evidence(state.retrieved_docs)

    # Generate hypothesis with LLM
    llm = runtime.context["llm"]
    prompt = f"""
    Based on this medical evidence, generate a clinical hypothesis:

    Evidence:
    {format_evidence(evidence)}

    Generate a hypothesis with:
    1. Clear statement
    2. Confidence level (0-1)
    3. Supporting citations
    4. Safety considerations
    """

    hypothesis_data = await llm.ainvoke(prompt)
    hypothesis = parse_hypothesis(hypothesis_data)

    # Store in conversation context
    conv_context = runtime.context["conversation_context"]
    conv_context.active_hypotheses.append(hypothesis)

    return {
        "messages": [{
            "role": "assistant",
            "content": format_hypothesis_response(hypothesis)
        }]
    }
```

**Implementation**: Feature **015-hypothesis-generation** (Nová feature!)

**Use Case**: Complex clinical queries requiring evidence synthesis

---

### 5. Reflection & Learning Pattern

#### BioAgents Approach:

```
Reflection Agent:
1. Extract key insights from conversation
2. Update methodology based on findings
3. Preserve conversation-level understanding
4. Guide next iteration steps
```

#### Adaptace pro Czech MedAI:

```python
async def reflection_agent_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Reflect on conversation and extract insights."""

    conv_context = runtime.context["conversation_context"]

    # Analyze conversation history
    insights = []

    # 1. Extract key medical findings
    medical_insights = extract_medical_insights(
        state.messages,
        state.retrieved_docs
    )

    # 2. Identify knowledge gaps
    gaps = identify_knowledge_gaps(
        conv_context.research_objectives,
        conv_context.cited_studies
    )

    # 3. Update research objectives
    updated_objectives = refine_objectives(
        conv_context.research_objectives,
        medical_insights,
        gaps
    )

    # 4. Suggest next steps
    next_steps = generate_next_steps(
        updated_objectives,
        gaps
    )

    # Store insights
    conv_context.clinical_insights.extend(medical_insights)
    conv_context.research_objectives = updated_objectives

    return {
        "messages": [{
            "role": "assistant",
            "content": format_reflection_summary(
                insights=medical_insights,
                gaps=gaps,
                next_steps=next_steps
            )
        }]
    }
```

**Implementation**: Feature **016-reflection-learning** (Nová feature!)

**Benefits**:
- ✅ Continuous learning from interactions
- ✅ Adaptive research strategy
- ✅ Gap identification for follow-ups

---

### 6. Job Queue Pattern (Background Processing)

#### BioAgents Approach:

```
BullMQ with Redis:
- Background job processing
- Horizontal scaling
- Job persistence
- Exponential backoff retries
- WebSocket progress notifications
- Bull Board admin dashboard
```

#### Adaptace pro Czech MedAI:

```python
from celery import Celery
from celery.result import AsyncResult

app = Celery('czech_medai', broker='redis://localhost:6379/0')

@app.task(bind=True, max_retries=3)
def deep_research_task(self, query: str, user_id: str):
    """Background task for deep research workflow."""

    try:
        # Initialize conversation context
        conv_context = ConversationContext(
            conversation_id=self.request.id,
            user_id=user_id,
            created_at=datetime.now()
        )

        # Run deep research workflow
        for iteration in range(max_iterations):
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'iteration': iteration, 'status': 'searching'}
            )

            # Execute research iteration
            results = await run_research_iteration(
                query=query,
                conv_context=conv_context
            )

            # Check if user feedback needed
            if needs_user_feedback(results):
                # Pause and wait for user input
                await wait_for_feedback(self.request.id)

            # Reflect and refine
            conv_context = await reflection_step(results, conv_context)

            if research_complete(conv_context):
                break

        # Final synthesis
        final_response = await synthesis_step(conv_context)

        return {
            'status': 'completed',
            'response': final_response,
            'insights': conv_context.clinical_insights
        }

    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)

# API endpoint
@app.post("/api/deep-research")
async def start_deep_research(query: str, user_id: str):
    """Start background deep research task."""
    task = deep_research_task.delay(query, user_id)

    return {
        "task_id": task.id,
        "status_url": f"/api/task-status/{task.id}"
    }

@app.get("/api/task-status/{task_id}")
async def get_task_status(task_id: str):
    """Get task status and progress."""
    result = AsyncResult(task_id, app=app)

    if result.state == 'PROGRESS':
        return {
            "state": result.state,
            "meta": result.info
        }
    elif result.state == 'SUCCESS':
        return {
            "state": result.state,
            "result": result.result
        }
    else:
        return {"state": result.state}
```

**Implementation**: Feature **017-background-jobs** (Nová feature!)

**Benefits**:
- ✅ Non-blocking deep research
- ✅ Progress tracking
- ✅ Resume on failure
- ✅ Scalability

---

### 7. Modular Agent Design

#### BioAgents Approach:

```
7 Specialized Agents:
1. File Upload Agent
2. Planning Agent
3. Literature Agent
4. Analysis Agent
5. Hypothesis Agent
6. Reflection Agent
7. Reply Agent
```

#### Czech MedAI Agent Architecture:

```
Core Agents (Phase 1):
1. Drug Agent (SÚKL-mcp)
2. Pricing Agent (VZP)
3. PubMed Agent (BioMCP)
4. Guidelines Agent (ČLS JEP)

Orchestration Agents (Phase 2):
5. Supervisor Agent (Intent routing)
6. Citation Agent (Reference management)
7. Synthesizer Agent (Response generation)

Advanced Agents (Phase 3+):
8. Planning Agent (Research task generation) ← BioAgents
9. Hypothesis Agent (Evidence synthesis) ← BioAgents
10. Reflection Agent (Learning & insights) ← BioAgents
11. Analysis Agent (Data interpretation)
12. Patient Context Agent (EMR integration)
```

**LangGraph Implementation**:

```python
# Modular node design
async def planning_agent_node(state: State, runtime: Runtime[Context]):
    """Generate research plan from user query."""
    # Independent, reusable module
    pass

async def hypothesis_agent_node(state: State, runtime: Runtime[Context]):
    """Generate hypotheses from evidence."""
    # Independent, reusable module
    pass

# Orchestration
graph = (
    StateGraph(State, context_schema=Context)
    .add_node("planning", planning_agent_node)
    .add_node("drug", drug_agent_node)
    .add_node("pubmed", pubmed_agent_node)
    .add_node("hypothesis", hypothesis_agent_node)
    .add_node("reflection", reflection_agent_node)
    .add_conditional_edges("planning", route_to_agents)
    .add_edge("hypothesis", "reflection")
    .compile()
)
```

---

### 8. Custom Knowledge Base Pattern

#### BioAgents Approach:

```
Custom Knowledge:
1. Place documents in docs/ directory
2. Automatic embedding on startup
3. Vector DB indexing
4. Semantic search with reranking
```

#### Adaptace pro Czech MedAI:

```python
# Custom Czech Guidelines Knowledge Base

from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings

class CzechGuidelinesKnowledgeBase:
    """Custom knowledge base for ČLS JEP guidelines."""

    def __init__(self, docs_dir: str = "guidelines/"):
        self.docs_dir = docs_dir
        self.vectorstore = None
        self.embeddings = OpenAIEmbeddings()

    async def initialize(self):
        """Load and index all guidelines."""

        # 1. Load documents
        docs = []
        for file in Path(self.docs_dir).glob("**/*.pdf"):
            # Parse PDF
            parsed = parse_czech_medical_pdf(file)
            docs.extend(parsed)

        # 2. Create embeddings
        self.vectorstore = await SupabaseVectorStore.afrom_documents(
            documents=docs,
            embedding=self.embeddings,
            table_name="czech_guidelines"
        )

        logger.info(f"Indexed {len(docs)} guideline documents")

    async def search(
        self,
        query: str,
        top_k: int = 5,
        use_reranking: bool = True
    ) -> list[Document]:
        """Search guidelines with optional reranking."""

        # Vector search
        results = await self.vectorstore.asimilarity_search(
            query,
            k=top_k * 2 if use_reranking else top_k
        )

        # Optional: Cohere reranking
        if use_reranking:
            results = await self.rerank_with_cohere(query, results, top_k)

        return results

    async def rerank_with_cohere(
        self,
        query: str,
        docs: list[Document],
        top_k: int
    ) -> list[Document]:
        """Rerank with Cohere for better relevance."""
        import cohere

        co = cohere.Client(os.getenv("COHERE_API_KEY"))

        # Rerank
        reranked = co.rerank(
            query=query,
            documents=[d.page_content for d in docs],
            top_n=top_k,
            model="rerank-multilingual-v2.0"  # Supports Czech!
        )

        # Return reranked docs
        return [docs[r.index] for r in reranked]

# Usage in Guidelines Agent
async def guidelines_agent_node(state, runtime):
    kb = runtime.context["czech_guidelines_kb"]

    results = await kb.search(
        query=extract_query(state.messages[-1]),
        top_k=5,
        use_reranking=True
    )

    return {"retrieved_docs": results}
```

**Implementation**: Feature **006-guidelines-agent** (Update)

**Setup**:
```bash
# Add ČLS JEP PDFs to guidelines/ directory
mkdir -p guidelines/
cp ~/Downloads/cls-jep-*.pdf guidelines/

# Initialize on startup
python -m agent.init_knowledge_base
```

---

## 🗺️ Roadmap Update: Nové Features

Basedna BioAgents inspiraci přidáváme **5 nových features**:

### Phase 3.5: Advanced Intelligence (Weeks 13-16)

**013-workflow-modes** (6 dní, MEDIUM)
- Quick Answer Mode (single-shot)
- Deep Analysis Mode (iterative)
- User mode selection
- Progress tracking

**014-knowledge-orchestration** (5 dní, MEDIUM)
- Multi-backend search orchestration
- Result merging & deduplication
- Cohere reranking (optional)

**015-hypothesis-generation** (7 dní, HIGH)
- Clinical hypothesis synthesis
- Evidence-based confidence scoring
- Safety considerations
- Citation tracking

**016-reflection-learning** (6 dní, MEDIUM)
- Conversation insights extraction
- Knowledge gap identification
- Research objective refinement
- Next steps suggestion

**017-background-jobs** (8 dní, HIGH)
- Celery/Redis job queue
- Deep research async processing
- Progress notifications (WebSocket)
- Task persistence & retry

---

## 📋 Implementation Checklist

### Immediate (Foundation Phase)

- [ ] Update State schema s message/conversation separation
- [ ] Add ConversationContext dataclass
- [ ] Update Context TypedDict s workflow mode
- [ ] Document state management patterns

### Phase 2 (Integration)

- [ ] Implement knowledge orchestrator
- [ ] Add Cohere reranking support
- [ ] Setup custom guidelines KB

### Phase 3.5 (Advanced Intelligence)

- [ ] Implement workflow mode routing
- [ ] Create planning agent
- [ ] Create hypothesis agent
- [ ] Create reflection agent
- [ ] Setup Celery job queue
- [ ] Add WebSocket progress notifications

---

## 🔧 Configuration Updates

### .env additions:

```bash
# ==================================================
# Advanced Features (BioAgents-inspired)
# ==================================================

# Workflow Modes
DEFAULT_WORKFLOW_MODE=quick  # quick | deep
ENABLE_DEEP_RESEARCH=true
MAX_RESEARCH_ITERATIONS=5

# Knowledge Orchestration
ENABLE_COHERE_RERANKING=false
COHERE_API_KEY=your_key_here
RERANK_MODEL=rerank-multilingual-v2.0

# Background Jobs
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
ENABLE_JOB_QUEUE=false  # Enable for production

# Hypothesis Generation
HYPOTHESIS_CONFIDENCE_THRESHOLD=0.7
ENABLE_SAFETY_CHECKS=true

# Reflection & Learning
ENABLE_CONVERSATION_MEMORY=true
MAX_CONVERSATION_HISTORY=100
ENABLE_INSIGHT_EXTRACTION=true
```

---

## 📚 References

- **BioAgents Repository**: https://github.com/bio-xyz/BioAgents
- **Cohere Rerank**: https://docs.cohere.com/docs/reranking
- **Celery**: https://docs.celeryq.dev/
- **BullMQ equivalent**: Celery + Redis

---

## 🎯 Key Takeaways

**BioAgents → Czech MedAI Adaptace**:

1. ✅ **Dual Workflow**: Quick vs Deep research modes
2. ✅ **State Management**: Message (ephemeral) vs Conversation (persistent)
3. ✅ **Multi-Backend Search**: SÚKL + BioMCP + Guidelines + VZP
4. ✅ **Hypothesis-Driven**: Evidence synthesis s citations
5. ✅ **Reflection**: Learning & insight extraction
6. ✅ **Background Jobs**: Async deep research
7. ✅ **Modular Agents**: Reusable, composable nodes
8. ✅ **Custom Knowledge**: Auto-indexed ČLS JEP guidelines

**Benefit**: Czech MedAI získává pokročilé research capabilities při zachování focus na české medicínské prostředí! 🚀

---

**Version**: 1.0.0
**Last Updated**: 2026-01-14
**Maintainer**: Czech MedAI Team
**Inspired by**: BioAgents (bio-xyz)
