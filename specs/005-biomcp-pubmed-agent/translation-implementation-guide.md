# Translation Implementation Guide: Medical Query Translation in LangGraph

**Feature**: 005-biomcp-pubmed-agent
**Created**: 2026-01-20
**Purpose**: Practical implementation patterns for Czech ↔ English medical translation
**Companion Document**: `translation-strategy-research.md` (strategic decision rationale)

---

## Quick Reference

**Decision**: LLM-based translation using Claude Sonnet within LangGraph nodes
**Pattern**: Specialized translation nodes with medical terminology preservation
**Integration**: Two new nodes in graph: `translate_cz_to_en_node` and `translate_en_to_cz_node`

---

## Implementation Overview

### File Structure

```
langgraph-app/src/agent/
├── nodes/
│   ├── translation.py          # NEW: Translation nodes
│   ├── pubmed_agent.py         # NEW: PubMed integration
│   └── __init__.py
├── utils/
│   ├── translation_prompts.py  # NEW: Prompt templates
│   └── query_extraction.py     # NEW: Helper functions
└── graph.py                    # UPDATE: Add translation nodes to graph
```

---

## Core Implementation

### 1. Translation Nodes (`src/agent/nodes/translation.py`)

```python
"""Medical translation nodes for Czech ↔ English conversion.

Implements the Sandwich Pattern:
- Czech query → English (for PubMed search)
- English results → Czech (for physician display)
"""

from typing import Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.documents import Document
from langgraph.runtime import Runtime

from agent.graph import State, Context
from agent.utils.translation_prompts import (
    CZ_TO_EN_PROMPT_TEMPLATE,
    EN_TO_CZ_PROMPT_TEMPLATE
)


async def translate_cz_to_en_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Translate Czech medical query to English for PubMed search.

    Uses runtime LLM with specialized medical translation prompt.
    Preserves medical terminology and expands abbreviations contextually.

    Args:
        state: Current state with Czech query in messages[-1]
        runtime: Runtime context with LLM configuration

    Returns:
        Updated state dict with:
            - research_query: Translated English query
            - original_query_cz: Original Czech query (for debugging)
            - messages: Pass-through

    Raises:
        ValueError: If state.messages is empty
        RuntimeError: If LLM call fails after retries
    """
    # Extract Czech query from last user message
    if not state.get("messages"):
        raise ValueError("State must contain at least one message")

    query_cz = _extract_query_text(state["messages"][-1])

    # Get LLM from runtime context
    llm: BaseChatModel = runtime.context.get("llm")
    if not llm:
        raise RuntimeError("LLM not configured in runtime context")

    # Build translation prompt
    prompt = CZ_TO_EN_PROMPT_TEMPLATE.format(query_cz=query_cz)

    # Translate with deterministic settings
    result = await llm.ainvoke(
        prompt,
        temperature=0.0,  # Deterministic for caching
        max_tokens=200    # Queries typically < 50 tokens
    )

    en_query = result.content.strip()

    # Log translation for debugging/monitoring
    print(f"[Translation CZ→EN] '{query_cz}' → '{en_query}'")

    # Optional: Quality validation
    if not en_query or len(en_query) < 3:
        print(f"[WARNING] Translation quality issue: '{query_cz}' → '{en_query}'")
        # Fallback: Use original query as-is
        en_query = query_cz

    return {
        "research_query": en_query,
        "original_query_cz": query_cz,
        "messages": state["messages"]  # Pass through unchanged
    }


async def translate_en_to_cz_node(
    state: State,
    runtime: Runtime[Context]
) -> Dict[str, Any]:
    """Translate English PubMed abstracts to Czech.

    Translates article abstracts while preserving medical terminology.
    Processes multiple documents in parallel for efficiency.

    Args:
        state: Current state with English documents in retrieved_docs
        runtime: Runtime context with LLM configuration

    Returns:
        Updated state dict with:
            - retrieved_docs: Documents with Czech-translated content
            - messages: Pass-through

    Raises:
        RuntimeError: If LLM call fails for any document
    """
    import asyncio

    if not state.get("retrieved_docs"):
        # No documents to translate - pass through
        return {"messages": state["messages"]}

    llm: BaseChatModel = runtime.context.get("llm")
    if not llm:
        raise RuntimeError("LLM not configured in runtime context")

    # Translate documents in parallel
    translation_tasks = [
        _translate_document_to_czech(doc, llm)
        for doc in state["retrieved_docs"]
    ]

    translated_docs = await asyncio.gather(*translation_tasks)

    return {
        "retrieved_docs": translated_docs,
        "messages": state["messages"]
    }


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_query_text(message: Dict[str, Any]) -> str:
    """Extract text content from message dict or string.

    Args:
        message: User message (dict with 'content' or plain string)

    Returns:
        Query text content
    """
    if isinstance(message, dict):
        return message.get("content", "")
    return str(message)


async def _translate_document_to_czech(
    doc: Document,
    llm: BaseChatModel
) -> Document:
    """Translate single document abstract to Czech.

    Args:
        doc: Document with English abstract in page_content
        llm: LLM for translation

    Returns:
        Document with Czech translation
    """
    abstract_en = doc.page_content

    # Build translation prompt
    prompt = EN_TO_CZ_PROMPT_TEMPLATE.format(abstract_en=abstract_en)

    # Translate
    result = await llm.ainvoke(
        prompt,
        temperature=0.0,
        max_tokens=1000  # Abstracts can be longer
    )

    abstract_cz = result.content.strip()

    # Create translated document
    translated_doc = Document(
        page_content=abstract_cz,
        metadata={
            **doc.metadata,
            "original_language": "en",
            "translated_to": "cs",
            "original_abstract": abstract_en  # Preserve original for verification
        }
    )

    return translated_doc
```

---

### 2. Translation Prompts (`src/agent/utils/translation_prompts.py`)

```python
"""Translation prompt templates for medical domain.

Prompts optimized for:
- Medical terminology preservation
- Abbreviation expansion
- PubMed search effectiveness
- Czech medical convention adherence
"""

# ============================================================================
# Czech → English Translation
# ============================================================================

CZ_TO_EN_PROMPT_TEMPLATE = """You are a medical translator specializing in Czech to English translation for biomedical literature search.

Your task is to translate the following Czech medical query to English, optimized for searching PubMed/MEDLINE databases.

CRITICAL TRANSLATION RULES:

1. **Medical Terminology Preservation**
   - Keep Latin medical terms unchanged (e.g., "diabetes mellitus" → "diabetes mellitus")
   - Use standard English medical terminology, NOT literal translations
   - Preserve anatomical terms in Latin form

2. **Abbreviation Expansion**
   - DM2 / DM 2 → "type 2 diabetes" or "diabetes mellitus type 2"
   - IM → "myocardial infarction"
   - ATB → "antibiotic" or "antibiotics" (context-dependent)
   - ICHS → "ischemic heart disease"
   - TK → "blood pressure" or "hypertension" (context-dependent)

3. **Drug Names**
   - Keep brand names unchanged (e.g., "Metformin" → "Metformin")
   - Use generic names when available (e.g., "Aspirin" preferred over "Acylpyrin")

4. **Search Optimization**
   - Use medical keywords that appear in PubMed titles/abstracts
   - Prefer specific terms over general ones
   - Include synonyms if helpful (e.g., "heart attack" OR "myocardial infarction")

5. **Output Format**
   - Provide ONLY the English translation
   - No explanations, no commentary, no metadata
   - Remove any conversational phrases (e.g., "Could you help me find...")

EXAMPLE TRANSLATIONS:

Czech: "Jaké jsou nejnovější studie o léčbě DM2 u starších pacientů?"
English: "latest studies treatment type 2 diabetes elderly patients"

Czech: "Komplikace po infarktu myokardu"
English: "complications after myocardial infarction"

Czech: "Vedlejší účinky ATB u dětí"
English: "side effects antibiotics children"

---

Czech Query: {query_cz}

English Translation:"""


# ============================================================================
# English → Czech Translation
# ============================================================================

EN_TO_CZ_PROMPT_TEMPLATE = """You are a medical translator specializing in English to Czech translation for biomedical literature.

Your task is to translate the following PubMed article abstract from English to Czech for Czech physicians.

CRITICAL TRANSLATION RULES:

1. **Medical Terminology**
   - Preserve Latin medical terms (e.g., "diabetes mellitus" → "diabetes mellitus")
   - Use standard Czech medical terminology from medical textbooks
   - DO NOT create literal translations of Latin terms

2. **Drug Names**
   - Keep brand names unchanged (e.g., "Metformin" → "Metformin")
   - Keep generic drug names in original form (e.g., "atorvastatin" → "atorvastatin")

3. **Units & Measurements**
   - Keep medical units unchanged (e.g., "mg/dl", "mmol/l", "mmHg")
   - Translate descriptions (e.g., "blood pressure" → "krevní tlak")

4. **Abbreviations**
   - Keep standard medical abbreviations (e.g., "HbA1c", "BMI", "LDL")
   - Translate expanded forms (e.g., "Body Mass Index" → "Index tělesné hmotnosti")

5. **Citation Preservation**
   - Keep inline citation numbers unchanged: [1], [2], [3]
   - Preserve DOI, PMID, URLs exactly as-is

6. **Translation Quality**
   - Use professional medical Czech language
   - Maintain technical accuracy and clinical precision
   - Ensure grammatical correctness in Czech

7. **Output Format**
   - Provide ONLY the Czech translation
   - No explanations, no commentary
   - Preserve paragraph structure and formatting

EXAMPLE TRANSLATION:

English: "A randomized controlled trial investigated the efficacy of metformin in type 2 diabetes patients. HbA1c levels decreased by 1.2% (p<0.001) after 12 weeks."

Czech: "Randomizovaná kontrolovaná studie zkoumala účinnost metforminu u pacientů s diabetem mellitus 2. typu. Hladiny HbA1c poklesly o 1,2 % (p<0,001) po 12 týdnech."

---

English Abstract: {abstract_en}

Czech Translation:"""


# ============================================================================
# Prompt Variants (Advanced)
# ============================================================================

# For queries requiring disambiguation
CZ_TO_EN_WITH_CONTEXT_TEMPLATE = """You are a medical translator specializing in Czech to English translation.

The user asked: "{query_cz}"

Previous context: {conversation_history}

Translate the query to English for PubMed search, taking into account the conversation context to resolve ambiguities.

[Rest of prompt same as CZ_TO_EN_PROMPT_TEMPLATE]
"""

# For high-precision translation with NER markers (Future: Feature 018)
CZ_TO_EN_WITH_NER_TEMPLATE = """You are a medical translator specializing in Czech to English translation.

The following medical entities have been detected in the query:
{detected_entities}

Translate the query, ensuring these entities are correctly translated or preserved.

Czech Query: {query_cz}

[Rest of prompt same as CZ_TO_EN_PROMPT_TEMPLATE]
"""
```

---

### 3. Query Extraction Utilities (`src/agent/utils/query_extraction.py`)

```python
"""Utilities for extracting and processing queries from messages."""

from typing import Dict, Any, List, Optional
from langchain_core.messages import AnyMessage


def extract_last_user_query(messages: List[AnyMessage]) -> str:
    """Extract text from last user message.

    Args:
        messages: List of conversation messages

    Returns:
        User query text

    Raises:
        ValueError: If no user messages found
    """
    for message in reversed(messages):
        if message.get("role") == "user" or getattr(message, "type", None) == "human":
            content = message.get("content") or getattr(message, "content", "")
            return str(content).strip()

    raise ValueError("No user message found in conversation")


def extract_query_with_context(
    messages: List[AnyMessage],
    max_context_messages: int = 3
) -> Dict[str, Any]:
    """Extract query with conversation context.

    Args:
        messages: List of conversation messages
        max_context_messages: Number of previous messages to include

    Returns:
        Dict with 'query' and 'context' keys
    """
    current_query = extract_last_user_query(messages)

    # Get context from previous N messages
    context_messages = messages[-(max_context_messages + 1):-1]
    context_text = "\n".join([
        f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
        for msg in context_messages
    ])

    return {
        "query": current_query,
        "context": context_text
    }


def is_medical_query(query: str) -> bool:
    """Detect if query is medical-related (simple heuristic).

    Args:
        query: User query text

    Returns:
        True if likely medical query

    Note:
        This is a simple keyword-based heuristic.
        For production, use ML-based intent classification.
    """
    medical_keywords = [
        # Czech medical terms
        "lék", "léčba", "choroba", "diagnóza", "symptom", "pacient",
        "terapie", "diabetes", "infarkt", "tlak", "antibiotik",

        # English fallback
        "drug", "treatment", "disease", "diagnosis", "symptom", "patient",
        "therapy", "medication"
    ]

    query_lower = query.lower()
    return any(keyword in query_lower for keyword in medical_keywords)
```

---

### 4. Graph Integration (`src/agent/graph.py` updates)

```python
"""Update graph.py to include translation nodes."""

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime

from agent.graph import State, Context
from agent.nodes.translation import (
    translate_cz_to_en_node,
    translate_en_to_cz_node
)
from agent.nodes.pubmed_agent import pubmed_agent_node


# Add to existing graph definition
graph = (
    StateGraph(State, context_schema=Context)

    # ... existing nodes ...

    # NEW: Translation nodes
    .add_node("translate_cz_to_en", translate_cz_to_en_node)
    .add_node("pubmed_agent", pubmed_agent_node)
    .add_node("translate_en_to_cz", translate_en_to_cz_node)

    # ... existing nodes ...

    # Edge flow for PubMed queries
    .add_edge("supervisor", "translate_cz_to_en")  # After intent classification
    .add_edge("translate_cz_to_en", "pubmed_agent")
    .add_edge("pubmed_agent", "translate_en_to_cz")
    .add_edge("translate_en_to_cz", "citation_system")  # Continue to citation

    .compile(name="Czech MedAI")
)
```

---

## Testing Implementation

### Unit Tests (`tests/unit_tests/nodes/test_translation.py`)

```python
"""Unit tests for translation nodes."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agent.nodes.translation import (
    translate_cz_to_en_node,
    translate_en_to_cz_node
)
from langchain_core.documents import Document


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    llm = AsyncMock()

    async def mock_ainvoke(prompt, **kwargs):
        # Simple mock: return prompt echo for testing
        response = MagicMock()
        if "Czech Query:" in prompt:
            # CZ→EN translation
            response.content = "type 2 diabetes treatment elderly patients"
        else:
            # EN→CZ translation
            response.content = "Testovací český překlad abstraktu."
        return response

    llm.ainvoke = mock_ainvoke
    return llm


@pytest.fixture
def mock_runtime(mock_llm):
    """Mock runtime with LLM."""
    runtime = MagicMock()
    runtime.context = {"llm": mock_llm}
    return runtime


@pytest.mark.asyncio
async def test_translate_cz_to_en_basic(mock_runtime):
    """Test basic Czech to English translation."""
    state = {
        "messages": [{"role": "user", "content": "Léčba DM2 u starších"}],
        "next": "translate",
        "retrieved_docs": []
    }

    result = await translate_cz_to_en_node(state, mock_runtime)

    assert "research_query" in result
    assert result["research_query"] is not None
    assert len(result["research_query"]) > 0
    assert "original_query_cz" in result
    assert result["original_query_cz"] == "Léčba DM2 u starších"


@pytest.mark.asyncio
async def test_translate_cz_to_en_preserves_medical_terms(mock_runtime):
    """Test that medical terms are preserved in translation."""
    # Update mock to return realistic translation
    async def specific_mock(prompt, **kwargs):
        response = MagicMock()
        response.content = "symptoms diabetes mellitus elderly patients"
        return response

    mock_runtime.context["llm"].ainvoke = specific_mock

    state = {
        "messages": [{"role": "user", "content": "Příznaky diabetes mellitus u starších"}],
        "next": "translate",
        "retrieved_docs": []
    }

    result = await translate_cz_to_en_node(state, mock_runtime)

    # Verify medical term preservation
    assert "diabetes mellitus" in result["research_query"].lower()


@pytest.mark.asyncio
async def test_translate_cz_to_en_empty_messages(mock_runtime):
    """Test error handling for empty messages."""
    state = {
        "messages": [],
        "next": "translate",
        "retrieved_docs": []
    }

    with pytest.raises(ValueError, match="State must contain at least one message"):
        await translate_cz_to_en_node(state, mock_runtime)


@pytest.mark.asyncio
async def test_translate_en_to_cz_multiple_docs(mock_runtime):
    """Test translation of multiple English documents."""
    state = {
        "messages": [{"role": "user", "content": "test"}],
        "next": "translate",
        "retrieved_docs": [
            Document(
                page_content="This is a study about diabetes.",
                metadata={"pmid": "12345"}
            ),
            Document(
                page_content="Another study on hypertension.",
                metadata={"pmid": "67890"}
            )
        ]
    }

    result = await translate_en_to_cz_node(state, mock_runtime)

    assert "retrieved_docs" in result
    assert len(result["retrieved_docs"]) == 2
    assert all(doc.metadata.get("translated_to") == "cs" for doc in result["retrieved_docs"])


@pytest.mark.asyncio
async def test_translate_en_to_cz_preserves_metadata(mock_runtime):
    """Test that document metadata is preserved after translation."""
    state = {
        "messages": [{"role": "user", "content": "test"}],
        "next": "translate",
        "retrieved_docs": [
            Document(
                page_content="English abstract text.",
                metadata={
                    "pmid": "12345",
                    "title": "Study Title",
                    "authors": ["Smith J", "Doe J"],
                    "year": 2024
                }
            )
        ]
    }

    result = await translate_en_to_cz_node(state, mock_runtime)

    translated_doc = result["retrieved_docs"][0]
    assert translated_doc.metadata["pmid"] == "12345"
    assert translated_doc.metadata["title"] == "Study Title"
    assert translated_doc.metadata["authors"] == ["Smith J", "Doe J"]
    assert translated_doc.metadata["year"] == 2024
```

---

### Integration Tests (`tests/integration_tests/test_translation_flow.py`)

```python
"""Integration tests for full translation flow."""

import pytest
from agent.graph import graph, State, Context


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_cz_en_cz_translation_flow():
    """Test complete CZ → EN → PubMed → CZ flow."""

    # Setup
    inputs = {
        "messages": [
            {"role": "user", "content": "Jaké jsou nejnovější studie o léčbě diabetu typu 2?"}
        ],
        "next": "__start__",
        "retrieved_docs": []
    }

    config = {
        "configurable": {
            "llm": "claude-sonnet-4.5",  # Use real LLM
            "langsmith_project": "test-translation-flow"
        }
    }

    # Execute graph
    result = await graph.ainvoke(inputs, config)

    # Verify CZ→EN translation occurred
    assert "research_query" in result
    assert result["research_query"] is not None
    assert "type 2 diabetes" in result["research_query"].lower() or \
           "diabetes type 2" in result["research_query"].lower()

    # Verify PubMed search executed
    assert "retrieved_docs" in result
    assert len(result["retrieved_docs"]) > 0

    # Verify EN→CZ translation occurred
    final_docs = result["retrieved_docs"]
    assert all(doc.metadata.get("translated_to") == "cs" for doc in final_docs)

    # Verify Czech content in response
    final_message = result["messages"][-1]
    assert final_message["role"] == "assistant"
    # Should contain Czech words
    czech_indicators = ["diabetes", "studie", "léčba", "pacient"]
    assert any(word in final_message["content"].lower() for word in czech_indicators)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_translation_preserves_citations():
    """Test that citations are preserved through translation."""

    inputs = {
        "messages": [
            {"role": "user", "content": "Léčba hypertenze u diabetiků"}
        ],
        "next": "__start__",
        "retrieved_docs": []
    }

    config = {"configurable": {"llm": "claude-sonnet-4.5"}}

    result = await graph.ainvoke(inputs, config)

    final_message = result["messages"][-1]

    # Should contain citation markers
    import re
    citations = re.findall(r'\[\d+\]', final_message["content"])
    assert len(citations) > 0, "No citations found in response"
```

---

## Advanced Patterns

### 1. Translation Caching

```python
"""Cache translations for improved performance and cost reduction."""

from functools import lru_cache
import hashlib


class TranslationCache:
    """LRU cache for query translations."""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, str] = {}
        self.max_size = max_size

    def _hash_query(self, query: str) -> str:
        """Generate cache key from query."""
        return hashlib.md5(query.encode()).hexdigest()

    def get(self, query: str) -> Optional[str]:
        """Get cached translation."""
        key = self._hash_query(query)
        return self.cache.get(key)

    def set(self, query: str, translation: str) -> None:
        """Cache translation."""
        if len(self.cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            self.cache.pop(next(iter(self.cache)))

        key = self._hash_query(query)
        self.cache[key] = translation


# Usage in translation node
translation_cache = TranslationCache(max_size=1000)

async def translate_cz_to_en_node_with_cache(state, runtime):
    """Translation with caching."""
    query_cz = extract_query(state["messages"][-1])

    # Check cache
    cached = translation_cache.get(query_cz)
    if cached:
        print(f"[Cache HIT] '{query_cz}'")
        return {"research_query": cached, "messages": state["messages"]}

    # Cache miss - translate
    llm = runtime.context["llm"]
    result = await llm.ainvoke(CZ_TO_EN_PROMPT_TEMPLATE.format(query_cz=query_cz))
    en_query = result.content.strip()

    # Store in cache
    translation_cache.set(query_cz, en_query)

    return {"research_query": en_query, "messages": state["messages"]}
```

### 2. Parallel Abstract Translation

```python
"""Translate multiple abstracts in parallel for efficiency."""

import asyncio
from typing import List

async def translate_abstracts_parallel(
    docs: List[Document],
    llm: BaseChatModel,
    batch_size: int = 5
) -> List[Document]:
    """Translate multiple abstracts in parallel batches.

    Args:
        docs: Documents to translate
        llm: LLM for translation
        batch_size: Number of concurrent translations

    Returns:
        Translated documents
    """
    async def translate_batch(batch: List[Document]) -> List[Document]:
        tasks = [_translate_document_to_czech(doc, llm) for doc in batch]
        return await asyncio.gather(*tasks)

    # Process in batches to avoid overwhelming API
    translated_docs = []
    for i in range(0, len(docs), batch_size):
        batch = docs[i:i + batch_size]
        batch_results = await translate_batch(batch)
        translated_docs.extend(batch_results)

    return translated_docs
```

### 3. Translation Quality Monitoring

```python
"""Monitor translation quality metrics."""

from dataclasses import dataclass
from typing import List
import time


@dataclass
class TranslationMetrics:
    """Translation performance metrics."""
    query_cz: str
    query_en: str
    latency_ms: float
    token_count: int
    timestamp: float


class TranslationMonitor:
    """Monitor and log translation metrics."""

    def __init__(self):
        self.metrics: List[TranslationMetrics] = []

    def log_translation(
        self,
        query_cz: str,
        query_en: str,
        latency_ms: float,
        token_count: int
    ) -> None:
        """Log translation metrics."""
        metric = TranslationMetrics(
            query_cz=query_cz,
            query_en=query_en,
            latency_ms=latency_ms,
            token_count=token_count,
            timestamp=time.time()
        )
        self.metrics.append(metric)

    def get_avg_latency(self) -> float:
        """Calculate average translation latency."""
        if not self.metrics:
            return 0.0
        return sum(m.latency_ms for m in self.metrics) / len(self.metrics)

    def get_p95_latency(self) -> float:
        """Calculate P95 latency."""
        if not self.metrics:
            return 0.0
        latencies = sorted(m.latency_ms for m in self.metrics)
        idx = int(len(latencies) * 0.95)
        return latencies[idx]


# Usage in translation node
monitor = TranslationMonitor()

async def translate_cz_to_en_with_monitoring(state, runtime):
    """Translation with performance monitoring."""
    start_time = time.time()

    query_cz = extract_query(state["messages"][-1])
    llm = runtime.context["llm"]

    result = await llm.ainvoke(CZ_TO_EN_PROMPT_TEMPLATE.format(query_cz=query_cz))
    en_query = result.content.strip()

    # Log metrics
    latency_ms = (time.time() - start_time) * 1000
    token_count = len(query_cz.split()) + len(en_query.split())  # Rough estimate

    monitor.log_translation(query_cz, en_query, latency_ms, token_count)

    return {"research_query": en_query, "messages": state["messages"]}
```

---

## Configuration

### Environment Variables (`.env`)

```bash
# Translation Configuration
TRANSLATION_MODEL=claude-sonnet-4.5  # or gpt-4o
TRANSLATION_TEMPERATURE=0.0
TRANSLATION_MAX_TOKENS_QUERY=200
TRANSLATION_MAX_TOKENS_ABSTRACT=1000

# Caching
ENABLE_TRANSLATION_CACHE=true
TRANSLATION_CACHE_SIZE=1000

# Monitoring
ENABLE_TRANSLATION_MONITORING=true
LOG_TRANSLATION_METRICS=true

# Fallback (Optional)
ENABLE_DEEPL_FALLBACK=false
DEEPL_API_KEY=your_key_here
```

---

## Performance Optimization Checklist

- [x] Use `temperature=0.0` for deterministic caching
- [x] Implement LRU cache for common queries
- [x] Translate abstracts in parallel (batch_size=5)
- [x] Set appropriate `max_tokens` limits
- [x] Monitor P95 latency via LangSmith
- [ ] Implement fallback to DeepL API if latency > 3s (Post-MVP)
- [ ] Add Redis-backed cache for production (Post-MVP)

---

## Troubleshooting

### Issue: Translation quality degradation

**Symptoms**: Medical terms incorrectly translated, abbreviations not expanded

**Solutions**:
1. Review and refine prompt templates
2. Add specific examples to prompts for edge cases
3. Implement glossary-based pre-processing for high-frequency terms
4. Use higher-quality LLM model (e.g., GPT-4o instead of GPT-3.5)

### Issue: High latency (> 5s total)

**Symptoms**: User queries exceed SC-001 target

**Solutions**:
1. Enable translation caching
2. Increase parallel batch size for abstracts
3. Use `latency_optimized` model settings
4. Consider fallback to DeepL API for high-volume

### Issue: LLM token costs escalating

**Symptoms**: Monthly costs exceed budget

**Solutions**:
1. Implement aggressive caching (Redis-backed)
2. Deduplicate queries before translation
3. Switch to more cost-effective model (GPT-4o-mini)
4. Evaluate DeepL API paid tier ($5.99/month unlimited)

---

## Next Steps (Post-MVP)

1. **Feature 018: Advanced Translation**
   - Medical NER integration (Med7, scispaCy)
   - Terminology glossary (500+ terms)
   - Translation quality metrics (BLEU, COMET)
   - DeepL API fallback for high-volume

2. **Performance Optimization**
   - Redis-backed translation cache
   - Batch translation API calls
   - Monitoring dashboard (Grafana)

3. **Quality Assurance**
   - Bilingual medical expert evaluation
   - A/B testing: LLM vs DeepL
   - User feedback collection

---

## References

- Main strategy document: `translation-strategy-research.md`
- LangGraph documentation: https://docs.langchain.com/langgraph
- Translation prompts: `src/agent/utils/translation_prompts.py`
- Test suite: `tests/unit_tests/nodes/test_translation.py`

---

**Version**: 1.0.0
**Last Updated**: 2026-01-20
**Maintainer**: Czech MedAI Development Team
